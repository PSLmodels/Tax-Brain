import taxcalc as tc
import pandas as pd
import numpy as np
import behresp
from taxcalc.utils import (
    DIST_VARIABLES,
    DIFF_VARIABLES,
    create_distribution_table,
    create_difference_table,
)
from dask import compute, delayed
import dask.multiprocessing
from collections import defaultdict
from taxbrain.utils import weighted_sum, update_policy
from taxbrain.corporate_incidence import distribute as dist_corp
from typing import Union
from paramtools import ValidationError


class TaxBrain:

    FIRST_BUDGET_YEAR = tc.Policy.JSON_START_YEAR
    LAST_BUDGET_YEAR = tc.Policy.LAST_BUDGET_YEAR
    # Default list of variables saved for each year
    DEFAULT_VARIABLES = list(set(DIST_VARIABLES).union(set(DIFF_VARIABLES)))

    # add dictionary to hold version of the various models
    VERSIONS = {
        "Tax-Calculator": tc.__version__,
        "Behavioral-Responses": behresp.__version__,
    }

    def __init__(
        self,
        start_year: int,
        end_year: int = LAST_BUDGET_YEAR,
        microdata: Union[str, dict] = None,
        use_cps: bool = False,
        reform: Union[str, dict] = None,
        behavior: dict = None,
        assump=None,
        base_policy: Union[str, dict] = None,
        corp_revenue: Union[dict, list, np.array] = None,
        corp_incidence_assumptions: dict = None,
        verbose=False,
        stacked=False,
    ):
        """
        Constructor for the TaxBrain class

        Parameters
        ----------
        start_year: int
            First year in the analysis. Must be no earlier than the
            first year allowed in Tax-Calculator.
        end_year: int
            Last year in the analysis. Must be no later than the last
            year allowed in Tax-Calculator.
        microdata: str or Pandas DataFrame
            Either a path to a micro-data file or a Pandas DataFrame
            containing micro-data.
        use_cps: bool
            A boolean value to indicate whether or not the analysis should
            be run using the CPS file included in Tax-Calculator.
            Note: use_cps cannot be True if a file was also specified with
            the microdata parameter.
        reform: str or dict
            Individual income tax policy reform. Can be either a string
            pointing to a JSON reform file, or the contents of a JSON file,
            or a properly formatted JSON file.
        behavior: dict
            Individual behavior assumptions use by the Behavior-Response
            package.
        assump: str
            A string pointing to a JSON file containing user specified
            economic assumptions.
        base_policy: str or dict
            Individual income tax policy to use as the baseline for
            the analysis. This policy will be implemented in the base
            calculator instance as well as the reform Calculator
            before the user provided reform is implemented. Can either
            be a string pointing to a JSON reform file, the contents
            of a JSON file, or a properly formatted dictionary.
        corp_revenue: dict, list, or numpy array
            A set of corporate revenue estimates for a given set of
            years.  The estimates much line up with start_year and
            end_year.
        corp_incidence_assumptions: dict
            A dictionary summarizing the assumptions about the
            distribution of the corporate income tax.  See
            taxbrain.corporate_incidence.CI_params for an example.
        verbose: bool
            A boolean value indicated whether or not to write model
            progress reports.
        stacked: bool
            A boolean value indicating weather the provided reform is in the
            format used for stacked reform analysis

        Returns
        -------
        None
        """
        if not use_cps and microdata is None:
            raise ValueError("Must specify microdata or set 'use_cps' to True")
        assert isinstance(start_year, int) & isinstance(
            end_year, int
        ), "Start and end years must be integers"
        assert start_year <= end_year, (
            f"Specified end year, {end_year}, is before specified start year, "
            f"{start_year}."
        )
        assert TaxBrain.FIRST_BUDGET_YEAR <= start_year, (
            f"Specified start_year, {start_year}, comes before first known "
            f"budget year, {TaxBrain.FIRST_BUDGET_YEAR}."
        )
        assert end_year <= TaxBrain.LAST_BUDGET_YEAR, (
            f"Specified end_year, {end_year}, comes after last known "
            f"budget year, {TaxBrain.LAST_BUDGET_YEAR}."
        )
        if corp_revenue:
            assert (
                len(corp_revenue) == end_year - start_year + 1
            ), f"Corporate revenue is not given for each budget year"
        self.microdata = microdata
        self.use_cps = use_cps
        self.start_year = start_year
        self.end_year = end_year
        self.base_data = {yr: {} for yr in range(start_year, end_year + 1)}
        self.reform_data = {yr: {} for yr in range(start_year, end_year + 1)}
        self.corp_revenue = corp_revenue
        self.ci_params = corp_incidence_assumptions
        self.verbose = verbose
        self.stacked = stacked
        self.stacked_reforms = None  # only used if stacked is true

        # Process user inputs early to throw any errors quickly
        self.params = self._process_user_mods(reform, assump)
        self.params["behavior"] = behavior
        if base_policy:
            base_policy = self._process_user_mods(base_policy, None)
            self.params["base_policy"] = base_policy["policy"]
        else:
            self.params["base_policy"] = None

        self.has_run = False

    def run(
        self, varlist: list = DEFAULT_VARIABLES, client=None, num_workers=1
    ):
        """
        Run the calculators. TaxBrain will determine whether to do a static or
        partial equilibrium run based on the user's inputs when initializing
        the TaxBrain object.

        Parameters
        ----------
        varlist: list
            variables from the microdata to be stored in each year

        Returns
        -------
        None
        """
        if not isinstance(varlist, list):
            msg = f"'varlist' is of type {type(varlist)}. Must be a list."
            raise TypeError(msg)
        if self.stacked:
            base_calc, policy, records = self._make_stacked_objects()
            self._stacked_run(
                varlist, base_calc, policy, records, client, num_workers
            )
            del base_calc
        else:
            base_calc, reform_calc = self._make_calculators()
            if self.params["behavior"]:
                if self.verbose:
                    print("Running dynamic simulations")
                self._dynamic_run(
                    varlist, base_calc, reform_calc, client, num_workers
                )
            else:
                if self.verbose:
                    print("Running static simulations")
                self._static_run(
                    varlist, base_calc, reform_calc, client, num_workers
                )
            del base_calc, reform_calc

        setattr(self, "has_run", True)

    def weighted_totals(
        self, var: str, include_total: bool = False
    ) -> pd.DataFrame:
        """
        Create a pandas DataFrame that shows the weighted sum or a specified
        variable under the baseline policy, reform policy, and the difference
        between the two.

        Parameters
        ----------
        var: str
            Variable name for variable you want the weighted total of.
        include_total: bool
            If true the returned DataFrame will include a "total" columns

        Returns
        -------
        Pandas DataFrame
            A Pandas DataFrame with rows for the baseline total,
            reform total, and the difference between the two.
        """
        base_totals = {}
        reform_totals = {}
        differences = {}
        for year in range(self.start_year, self.end_year + 1):
            base_totals[year] = (
                self.base_data[year]["s006"] * self.base_data[year][var]
            ).sum()
            reform_totals[year] = (
                self.reform_data[year]["s006"] * self.reform_data[year][var]
            ).sum()
            differences[year] = reform_totals[year] - base_totals[year]
        table = pd.DataFrame(
            [base_totals, reform_totals, differences],
            index=["Base", "Reform", "Difference"],
        )
        if include_total:
            table["Total"] = table.sum(axis=1)
        return table

    def multi_var_table(
        self, varlist: list, calc: str, include_total: bool = False
    ) -> pd.DataFrame:
        """
        Create a Pandas DataFrame with multiple variables from the
        specified data source

        Parameters
        ----------
        varlist: list
            list of variables to include in the table
        calc: str
            specify reform or base calculator data, can take either
            `'REFORM'` or `'BASE'`
        include_total: bool
            If true the returned DataFrame will include a "total" column

        Returns
        -------
        df: Pandas DataFrame
            A Pandas DataFrame containing the weighted sum of each
            variable passed in the `varlist` argument for each year in
            the analysis.
        """
        if not isinstance(varlist, list):
            msg = f"'varlist' is of type {type(varlist)}. Must be a list."
            raise TypeError(msg)
        if calc.upper() == "REFORM":
            data = self.reform_data
        elif calc.upper() == "BASE":
            data = self.base_data
        else:
            raise ValueError("'calc' must be 'base' or 'reform'")
        data_dict = defaultdict(list)
        for year in range(self.start_year, self.end_year + 1):
            for var in varlist:
                data_dict[var] += [weighted_sum(data[year], var)]
        df = pd.DataFrame(
            data_dict, index=range(self.start_year, self.end_year + 1)
        )
        table = df.transpose()
        if include_total:
            table["Total"] = table.sum(axis=1)
        return table

    def distribution_table(
        self,
        year: int,
        groupby: str,
        income_measure: str,
        calc: str,
        pop_quantiles: bool = False,
    ) -> pd.DataFrame:
        """
        Method to create a distribution table

        Parameters
        ----------
        year: int
            which year the distribution table data should be from
        groupby: str
            determines how the rows in the table are sorted
            options: 'weighted_deciles', 'standard_income_bins',
            'soi_agi_bin'
        income_measure: str
            determines which variable is used to sort the rows in
            the table
            options: 'expanded_income' or 'expanded_income_baseline'
        calc: str
            which calculator to use, can take either
            `'REFORM'` or `'BASE'`
        calc: which calculator to use: base or reform
        pop_quantiles: bool
            whether or not weighted_deciles contain equal number of
            tax units (False) or people (True)

        Returns
        -------
        table: Pandas DataFrame
            distribution table
        """
        # pull desired data
        if calc.lower() == "base":
            data = self.base_data[year]
        elif calc.lower() == "reform":
            data = self.reform_data[year]
        else:
            raise ValueError("calc must be either BASE or REFORM")
        # minor data preparation before calling the function
        if pop_quantiles:
            data["count"] = data["s006"] * data["XTOT"]
        else:
            data["count"] = data["s006"]
        data["count_ItemDed"] = data["count"].where(data["c04470"] > 0.0, 0.0)
        data["count_StandardDed"] = data["count"].where(
            data["standard"] > 0.0, 0.0
        )
        data["count_AMT"] = data["count"].where(data["c09600"] > 0.0, 0.0)
        if income_measure == "expanded_income_baseline":
            base_income = self.base_data[year]["expanded_income"]
            data["expanded_income_baseline"] = base_income
        table = create_distribution_table(
            data, groupby, income_measure, pop_quantiles
        )
        return table

    def differences_table(
        self,
        year: int,
        groupby: str,
        tax_to_diff: str,
        pop_quantiles: bool = False,
    ) -> pd.DataFrame:
        """
        Method to create a differences table

        Parameters
        ----------
        year: int
            which year the difference table should be from
        groupby: str
            determines how the rows in the table are sorted
            options: 'weighted_deciles', 'standard_income_bins', 'soi_agi_bin'
        tax_to_diff: str
            which tax to take the difference of
            options: 'iitax', 'payrolltax', 'combined'
        pop_quantiles: bool
            whether weighted_deciles contain an equal number of tax
            units (False) or people (True)

        Returns
        -------
        table: Pandas DataFrame
            differences table
        """
        base_data = self.base_data[year]
        reform_data = self.reform_data[year]
        table = create_difference_table(
            base_data, reform_data, groupby, tax_to_diff, pop_quantiles
        )
        return table

    # ----- private methods -----
    def _taxcalc_advance(self, calc, varlist, year, reform=False):
        """
        This function advances the year used in Tax-Calculator, computes
        tax liability and rates, and saves the results to a dictionary.
        Args:
            calc (Tax-Calculator Calculator object): TC calculator
            varlist (list): variables to return
            year (int): year to begin advancing from
            reform (bool): whether Calculator object is for the reform policy

        Returns:
            tax_dict (dict): a dictionary of microdata with marginal tax
                rates and other information computed in TC
        """
        calc.advance_to_year(year)
        if self.corp_revenue is not None:
            if reform:
                calc = dist_corp(
                    calc,
                    self.corp_revenue,
                    year,
                    self.start_year,
                    self.ci_params,
                )
        calc.calc_all()
        df = calc.dataframe(varlist)

        return df

    def _behresp_advance(self, base_calc, reform_calc, varlist, year):
        """
        This function advances the year used in the Behavioral Responses
        model and saves the results to a dictionary.
        Args:
            calc1 (Tax-Calculator Calculator object): TC calculator
            year (int): year to begin advancing from
        Returns:
            tax_dict (dict): a dictionary of microdata with marginal tax
                rates and other information computed in TC
        """
        base_calc.advance_to_year(year)
        reform_calc.advance_to_year(year)
        if self.corp_revenue is not None:
            reform_calc = dist_corp(
                reform_calc,
                self.corp_revenue,
                year,
                self.start_year,
                self.ci_params,
            )
        base, reform = behresp.response(
            base_calc, reform_calc, self.params["behavior"], dump=True
        )
        base_df = base[varlist]
        reform_df = reform[varlist]

        return [base_df, reform_df]

    def _static_run(
        self, varlist, base_calc, reform_calc, client, num_workers
    ):
        """
        Run the calculator for a static analysis
        """
        if "s006" not in varlist:  # ensure weight is always included
            varlist.append("s006")
        lazy_values = []
        for yr in range(self.start_year, self.end_year + 1):
            lazy_values.extend(
                [
                    delayed(self._taxcalc_advance(base_calc, varlist, yr)),
                    delayed(
                        self._taxcalc_advance(
                            reform_calc, varlist, yr, reform=True
                        )
                    ),
                ]
            )
        if client:
            futures = client.compute(lazy_values, num_workers=num_workers)
            results = client.gather(futures)
        else:
            results = results = compute(
                *lazy_values,
                scheduler=dask.multiprocessing.get,
                num_workers=num_workers,
            )

        # add results to base and reform data
        yr = self.start_year
        for i in np.arange(0, len(results), 2):
            self.base_data[yr] = results[i]
            self.reform_data[yr] = results[i + 1]
            yr += 1

        del results

    def _dynamic_run(
        self, varlist, base_calc, reform_calc, client, num_workers
    ):
        """
        Run a dynamic response
        """
        if "s006" not in varlist:  # ensure weight is always included
            varlist.append("s006")
        lazy_values = []
        for yr in range(self.start_year, self.end_year + 1):
            lazy_values.extend(
                [
                    delayed(
                        self._behresp_advance(
                            base_calc, reform_calc, varlist, yr
                        )
                    )
                ]
            )
        if client:
            futures = client.compute(lazy_values, num_workers=num_workers)
            results = client.gather(futures)
        else:
            results = results = compute(
                *lazy_values,
                scheduler=dask.multiprocessing.get,
                num_workers=num_workers,
            )

        # add results to base and reform data
        for i in range(len(results)):
            yr = self.start_year + i
            self.base_data[yr] = results[i][0]
            self.reform_data[yr] = results[i][1]

        del results

    def _stacked_run(
        self, varlist, base_calc, policy, records, client, num_workers
    ):
        revenue_output = {}
        BW_len = self.end_year - self.start_year + 1
        # run the base calc first to get baseline results
        lazy_values = []
        for yr in range(self.start_year, self.end_year + 1):
            lazy_values.append(
                delayed(self._taxcalc_advance(base_calc, varlist, yr))
            )
        if client:
            futures = client.compute(lazy_values, num_workers=num_workers)
            results = client.gather(futures)
        else:
            results = results = compute(
                *lazy_values,
                scheduler=dask.multiprocessing.get,
                num_workers=num_workers,
            )
        # add results to data and revenue outputs
        revenue_output["Baseline"] = np.zeros(BW_len)
        yr = self.start_year
        # for i in np.arange(0, len(results), 2):
        for i, res in enumerate(results):
            self.base_data[yr] = res
            combined = (res["combined"] * res["s006"]).sum()
            revenue_output["Baseline"][yr - self.start_year] = combined
            yr += 1
        reform_list = list(self.stacked_reforms.keys())
        # Loop over different provisions
        for k, v in self.stacked_reforms.items():
            if self.verbose:
                print("Analyzing ", k)
            revenue_output[k] = np.zeros(BW_len)
            ref = policy.read_json_reform(v)
            # update Policy object with additional provisions
            policy.implement_reform(ref)
            # update Calculator object with new Policy object
            calc = tc.calculator.Calculator(policy=policy, records=records)
            # loop over each year in budget window
            for yr in np.arange(self.start_year, self.end_year + 1):
                calc.advance_to_year(yr)
                # change income in accordance with corp income tax
                # distributed across individual taxpayers
                if self.corp_revenue is not None:
                    calc = dist_corp(
                        calc,
                        self.corp_revenue,
                        yr,
                        self.start_year,
                        self.ci_params,
                    )
                # makes calculations on microdata
                calc.calc_all()
                # compute total revenue
                revenue_output[k][yr - self.start_year] = calc.weighted_total(
                    "combined"
                )
                # if we're on the last reform piece, save the data
                if k == reform_list[-1]:
                    self.reform_data[yr] = calc.dataframe(varlist)
        df = pd.DataFrame.from_dict(
            revenue_output,
            orient="Index",
            columns=np.arange(self.start_year, self.start_year + BW_len),
        )
        # Compute differences from one provision to another
        rev_est_tbl = df.diff()
        # Drop baseline revenue since reporting differences relative to baseline
        rev_est_tbl.drop(labels="Baseline", inplace=True)

        # Create totals across budget window
        tot_col = f"{self.start_year}-{self.end_year}"
        rev_est_tbl[tot_col] = rev_est_tbl[list(rev_est_tbl.columns)].sum(
            axis=1
        )
        # Create totals across provisions
        rev_est_tbl.loc["Total"] = rev_est_tbl.sum()

        # save the table as an attribute of the TaxBrain object
        setattr(self, "stacked_table", rev_est_tbl)

    def _process_user_mods(self, reform, assump):
        """
        Logic to process user mods and set self.params
        """

        def key_validation(actual_keys, required_keys, d_name):
            """
            Validate keys if reform or assump is passed as a dictionary
            """
            missing_keys = required_keys - actual_keys
            if missing_keys:
                msg = f"Required key(s) {missing_keys} missing from '{d_name}'"
                raise ValueError(msg)
            illegal_keys = actual_keys - required_keys
            if illegal_keys:
                msg = f"Illegal key(s) {illegal_keys} found in '{d_name}'"
                raise ValueError(msg)

        if isinstance(reform, dict):
            # If the reform is a dictionary, we'll leave it to Tax-Calculator
            # to catch errors in its implementation. Or, it's a stacked reform
            # and we will check that separately
            if isinstance(assump, str) or not assump:
                params = tc.Calculator.read_json_param_objects(None, assump)
            elif isinstance(assump, dict):
                actual_keys = set(assump.keys())
                required_keys = tc.Calculator.REQUIRED_ASSUMP_KEYS
                key_validation(actual_keys, required_keys, "assump")
                params = {**assump}
            else:
                raise TypeError(
                    "'assump' is not a string, dictionary, or None"
                )
            params["policy"] = reform
            # Check stacked reforms
            if self.stacked:
                pol = tc.Policy()
                full_policy = {}
                for name, subreform in reform.items():
                    # assume that if the reform is a string it's a JSON reform
                    # Otherwise the parameters are already a dictionary
                    if isinstance(subreform, str):
                        pol_params = tc.Policy.read_json_reform(subreform)
                    else:
                        m = "Reform must be valid JSON string or dictionary"
                        assert isinstance(subreform, dict), m
                        pol_params = subreform
                    try:
                        update_policy(pol, pol_params)
                    except ValidationError as e:
                        print(f"Validation error in {name}")
                        raise e
                    # update the full policy to save later
                    full_policy = {**full_policy, **pol_params}
                setattr(self, "stacked_reforms", reform)
                params["policy"] = full_policy
        elif isinstance(reform, str) or not reform:
            if isinstance(assump, str) or not assump:
                params = tc.Calculator.read_json_param_objects(reform, assump)
            elif isinstance(assump, dict):
                # Check to ensure that the assumption dictionary contains
                # all the needed keys. Tax-Calculator will check that they
                # are ultimately defined correctly when attempting to
                # use them.
                actual_keys = set(assump.keys())
                required_keys = tc.Calculator.REQUIRED_ASSUMP_KEYS
                key_validation(actual_keys, required_keys, "assump")
                params = tc.Calculator.read_json_param_objects(reform, None)
                for key in assump.keys():
                    params[key] = assump[key]
            else:
                raise TypeError(
                    "'assump' is not a string, dictionary, or None"
                )
        else:
            raise TypeError("'reform' is not a string, dictionary, or None")

        # confirm that all the expected keys are there
        required_keys = (
            tc.Calculator.REQUIRED_ASSUMP_KEYS
            | tc.Calculator.REQUIRED_REFORM_KEYS
        )
        assert set(params.keys()) == required_keys

        return params

    def _make_calculators(self):
        """
        This function creates the baseline and reform calculators used when
        the `run()` method is called
        """
        # Create two microsimulation calculators
        gd_base = tc.GrowDiff()
        gf_base = tc.GrowFactors()
        # apply user specified growdiff
        if self.params["growdiff_baseline"]:
            gd_base.update_growdiff(self.params["growdiff_baseline"])
            gd_base.apply_to(gf_base)
        # Baseline calculator
        if self.use_cps:
            records = tc.Records.cps_constructor(
                data=self.microdata, gfactors=gf_base
            )
        else:
            records = tc.Records(self.microdata, gfactors=gf_base)
        policy = tc.Policy(gf_base)
        if self.params["base_policy"]:
            update_policy(policy, self.params["base_policy"])
        base_calc = tc.Calculator(
            policy=policy, records=records, verbose=self.verbose
        )

        # Reform calculator
        # Initialize a policy object
        gd_reform = tc.GrowDiff()
        gf_reform = tc.GrowFactors()
        if self.params["growdiff_response"]:
            gd_reform.update_growdiff(self.params["growdiff_response"])
            gd_reform.apply_to(gf_reform)
        if self.use_cps:
            records = tc.Records.cps_constructor(
                data=self.microdata, gfactors=gf_reform
            )
        else:
            records = tc.Records(self.microdata, gfactors=gf_reform)
        policy = tc.Policy(gf_reform)
        if self.params["base_policy"]:
            update_policy(policy, self.params["base_policy"])
        update_policy(policy, self.params["policy"])

        # Initialize Calculator
        reform_calc = tc.Calculator(
            policy=policy, records=records, verbose=self.verbose
        )
        # delete all unneeded variables
        del gd_base, gd_reform, records, gf_base, gf_reform, policy
        return base_calc, reform_calc

    def _make_stacked_objects(self):
        """
        This method makes the base calculator and policy and records objects
        for stacked reforms. The difference between this and the standard
        _make_calcuators method is that this method
        only fully creates the baseline calculator. For the reform, it creates
        policy and records objects and implements any growth assumptions
        provided by the user.
        """
        # Create two microsimulation calculators
        gd_base = tc.GrowDiff()
        gf_base = tc.GrowFactors()
        # apply user specified growdiff
        if self.params["growdiff_baseline"]:
            gd_base.update_growdiff(self.params["growdiff_baseline"])
            gd_base.apply_to(gf_base)
        # Baseline calculator
        if self.use_cps:
            records = tc.Records.cps_constructor(
                data=self.microdata, gfactors=gf_base
            )
        else:
            records = tc.Records(self.microdata, gfactors=gf_base)
        policy = tc.Policy(gf_base)
        if self.params["base_policy"]:
            update_policy(policy, self.params["base_policy"])
        base_calc = tc.Calculator(
            policy=policy, records=records, verbose=self.verbose
        )

        # Reform calculator
        # Initialize a policy object
        gd_reform = tc.GrowDiff()
        gf_reform = tc.GrowFactors()
        if self.params["growdiff_response"]:
            gd_reform.update_growdiff(self.params["growdiff_response"])
            gd_reform.apply_to(gf_reform)
        if self.use_cps:
            records = tc.Records.cps_constructor(
                data=self.microdata, gfactors=gf_reform
            )
        else:
            records = tc.Records(self.microdata, gfactors=gf_reform)
        policy = tc.Policy(gf_reform)
        return base_calc, policy, records
