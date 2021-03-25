import taxcalc as tc
import pandas as pd
import behresp
from taxcalc.utils import (DIST_VARIABLES, DIFF_VARIABLES,
                           create_distribution_table, create_difference_table)
from dask import compute, delayed
from collections import defaultdict
from taxbrain.utils import weighted_sum, update_policy
from taxbrain.tbogusa import run_ogusa
from typing import Union


class TaxBrain:

    FIRST_BUDGET_YEAR = tc.Policy.JSON_START_YEAR
    LAST_BUDGET_YEAR = tc.Policy.LAST_BUDGET_YEAR
    # Default list of variables saved for each year
    DEFAULT_VARIABLES = list(set(DIST_VARIABLES).union(set(DIFF_VARIABLES)))

    # add dictionary to hold version of the various models
    VERSIONS = {
        "Tax-Calculator": tc.__version__,
        "Behavioral-Responses": behresp.__version__
    }

    def __init__(self, start_year: int, end_year: int = LAST_BUDGET_YEAR,
                 microdata: Union[str, pd.DataFrame] = None,
                 use_cps: bool = False,
                 reform: Union[str, dict] = None, behavior: dict = None,
                 assump=None, ogusa: bool = False,
                 base_policy: Union[str, dict] = None, verbose=False):
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
        ogusa: bool
            A boolean value to indicate whether or not the analysis should
            be run with OG-USA
        base_policy: str or dict
            Individual income tax policy to use as the baseline for
            the analysis. This policy will be implemented in the base
            calculator instance as well as the reform Calculator
            before the user provided reform is implemented. Can either
            be a string pointing to a JSON reform file, the contents
            of a JSON file, or a properly formatted dictionary.
        verbose: bool
            A boolean value indicated whether or not to write model
            progress reports.

        Returns
        -------
        None
        """
        if not use_cps and microdata is None:
            raise ValueError("Must specify microdata or set 'use_cps' to True")
        assert isinstance(start_year, int) & isinstance(end_year, int), (
            "Start and end years must be integers"
        )
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
        self.microdata = microdata
        self.use_cps = use_cps
        self.start_year = start_year
        self.end_year = end_year
        self.base_data = {yr: {} for yr in range(start_year, end_year + 1)}
        self.reform_data = {yr: {} for yr in range(start_year, end_year + 1)}
        self.verbose = verbose

        # Process user inputs early to throw any errors quickly
        self.params = self._process_user_mods(reform, assump)
        self.params["behavior"] = behavior
        self.ogusa = ogusa
        if base_policy:
            base_policy = self._process_user_mods(base_policy, None)
            self.params["base_policy"] = base_policy["policy"]
        else:
            self.params["base_policy"] = None

        self.has_run = False

    def run(self, varlist: list = DEFAULT_VARIABLES, client=None,
            num_workers=1):
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
        if self.ogusa:
            if self.verbose:
                print("Running OG-USA")
            if self.use_cps:
                data_source = "cps"
            else:
                data_source = "puf"
            og_results = run_ogusa(
                iit_reform=self.params["policy"],
                data_source=data_source, start_year=self.start_year,
                client=client, num_workers=num_workers)
            self._apply_ogusa(og_results)
        base_calc, reform_calc = self._make_calculators()
        if not isinstance(varlist, list):
            msg = f"'varlist' is of type {type(varlist)}. Must be a list."
            raise TypeError(msg)
        if self.params["behavior"]:
            if self.verbose:
                print("Running dynamic simulations")
            self._dynamic_run(varlist, base_calc, reform_calc)
        else:
            if self.verbose:
                print("Running static simulations")
            self._static_run(varlist, base_calc, reform_calc)
        setattr(self, "has_run", True)

        del base_calc, reform_calc

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
            base_totals[year] = (self.base_data[year]["s006"] *
                                 self.base_data[year][var]).sum()
            reform_totals[year] = (self.reform_data[year]["s006"] *
                                   self.reform_data[year][var]).sum()
            differences[year] = reform_totals[year] - base_totals[year]
        table = pd.DataFrame([base_totals, reform_totals, differences],
                             index=["Base", "Reform", "Difference"])
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
        df = pd.DataFrame(data_dict,
                          index=range(self.start_year, self.end_year + 1))
        table = df.transpose()
        if include_total:
            table["Total"] = table.sum(axis=1)
        return table

    def distribution_table(self, year: int, groupby: str,
                           income_measure: str, calc: str,
                           pop_quantiles: bool = False) -> pd.DataFrame:
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
        data["count_ItemDed"] = data["count"].where(
            data["c04470"] > 0., 0.
        )
        data["count_StandardDed"] = data["count"].where(
            data["standard"] > 0., 0.
        )
        data["count_AMT"] = data["count"].where(
            data["c09600"] > 0., 0.
        )
        if income_measure == "expanded_income_baseline":
            base_income = self.base_data[year]["expanded_income"]
            data["expanded_income_baseline"] = base_income
        table = create_distribution_table(data, groupby, income_measure,
                                          pop_quantiles)
        return table

    def differences_table(self, year: int, groupby: str, tax_to_diff: str,
                          pop_quantiles: bool = False) -> pd.DataFrame:
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
        table = create_difference_table(base_data, reform_data, groupby,
                                        tax_to_diff, pop_quantiles)
        return table

    # ----- private methods -----
    def _static_run(self, varlist, base_calc, reform_calc):
        """
        Run the calculator for a static analysis
        """
        if "s006" not in varlist:  # ensure weight is always included
            varlist.append("s006")

        for yr in range(self.start_year, self.end_year + 1):
            base_calc.advance_to_year(yr)
            reform_calc.advance_to_year(yr)
            # run calculations in parallel
            delay = [delayed(base_calc.calc_all()),
                     delayed(reform_calc.calc_all())]
            compute(*delay)
            self.base_data[yr] = base_calc.dataframe(varlist)
            self.reform_data[yr] = reform_calc.dataframe(varlist)

    def _dynamic_run(self, varlist, base_calc, reform_calc):
        """
        Run a dynamic response
        """
        if "s006" not in varlist:  # ensure weight is always included
            varlist.append("s006")
        for year in range(self.start_year, self.end_year + 1):
            base_calc.advance_to_year(year)
            reform_calc.advance_to_year(year)
            base, reform = behresp.response(base_calc, reform_calc,
                                            self.params["behavior"],
                                            dump=True)
            self.base_data[year] = base[varlist]
            self.reform_data[year] = reform[varlist]

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
            # to catch errors in its implementation
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
            raise TypeError(
                "'reform' is not a string, dictionary, or None"
            )

        # confirm that all the expected keys are there
        required_keys = (tc.Calculator.REQUIRED_ASSUMP_KEYS |
                         tc.Calculator.REQUIRED_REFORM_KEYS)
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
            records = tc.Records.cps_constructor(data=self.microdata,
                                                 gfactors=gf_base)
        else:
            records = tc.Records(self.microdata, gfactors=gf_base)
        policy = tc.Policy(gf_base)
        if self.params["base_policy"]:
            update_policy(policy, self.params["base_policy"])
        base_calc = tc.Calculator(policy=policy,
                                  records=records,
                                  verbose=self.verbose)

        # Reform calculator
        # Initialize a policy object
        gd_reform = tc.GrowDiff()
        gf_reform = tc.GrowFactors()
        if self.params["growdiff_response"]:
            gd_reform.update_growdiff(self.params["growdiff_response"])
            gd_reform.apply_to(gf_reform)
        if self.use_cps:
            records = tc.Records.cps_constructor(data=self.microdata,
                                                 gfactors=gf_reform)
        else:
            records = tc.Records(self.microdata, gfactors=gf_reform)
        policy = tc.Policy(gf_reform)
        if self.params["base_policy"]:
            update_policy(policy, self.params["base_policy"])
        update_policy(policy, self.params["policy"])

        # Initialize Calculator
        reform_calc = tc.Calculator(policy=policy, records=records,
                                    verbose=self.verbose)
        # delete all unneeded variables
        del gd_base, gd_reform, records, gf_base, gf_reform, policy
        return base_calc, reform_calc

    def _apply_ogusa(self, og_results):
        """
        Apply the results of the OG-USA run
        Parameters
        ----------
        og_results: Numpy array
            percentage changes in macro variables used to update grow
            factors

        Returns
        -------
        None
        """
        # changes in wage growth rates are at the 4th index
        wage_change = og_results
        gf = tc.GrowFactors()
        grow_diff = {}
        for i, yr in enumerate(range(self.start_year, self.end_year)):
            cur_val = gf.factor_value("AWAGE", yr)
            grow_diff[yr] = float(cur_val * (1 + wage_change[i]))
        final_growdiffs = {
            "AWAGE": grow_diff
        }
        self.params["growdiff_response"] = final_growdiffs
