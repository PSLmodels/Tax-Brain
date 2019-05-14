import copy
import taxcalc as tc
import pandas as pd
import behresp
from taxcalc.utils import (DIST_VARIABLES, DIFF_VARIABLES,
                           create_distribution_table, create_difference_table)
from dask import compute, delayed
from collections import defaultdict
from taxbrain.utils import weighted_sum


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

    def __init__(self, start_year, end_year=LAST_BUDGET_YEAR,
                 microdata=None, use_cps=False, reform=None,
                 behavior=None, assump=None, verbose=False):
        """
        Constructor for the TaxBrain class
        Parameters
        ----------
        start_year: First year in the analysis. Must be no earlier than the
                    first year allowed in Tax-Calculator.
        end_year: Last year in the analysis. Must be no later than the last
                  year allowed in Tax-Calculator.
        microdata: Either a path to a micro-data file or a Pandas DataFrame
                   containing micro-data.
        use_cps: A boolean value to indicate whether or not the analysis should
                 be run using the CPS file included in Tax-Calculator.
                 Note: use_cps cannot be True if a file was also specified with
                 the microdata parameter.
        reform: Individual income tax policy reform. Can be either a string
                pointing to a JSON reform file, or the contents of a JSON file.
        behavior: Individual behavior assumptions use by the Behavior-Response
                  package.
        assump: A string pointing to a JSON file containing user specified
                economic assumptions.
        verbose: A boolean value indicated whether or not to write model
                 progress reports.
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
        self.use_cps = use_cps
        self.start_year = start_year
        self.end_year = end_year
        self.base_data = {yr: {} for yr in range(start_year, end_year + 1)}
        self.reform_data = {yr: {} for yr in range(start_year, end_year + 1)}
        self.verbose = verbose

        # Process user inputs early to throw any errors quickly
        self.params = self._process_user_mods(reform, assump)
        self.params["behavior"] = behavior

        # Create two microsimulation calculators
        gd_base = tc.GrowDiff()
        gf_base = tc.GrowFactors()
        # apply user specified growdiff
        if self.params["growdiff_baseline"]:
            gd_base.update_growdiff(self.params["growdiff_baseline"])
            gd_base.apply_to(gf_base)
        # Baseline calculator
        if use_cps:
            records = tc.Records.cps_constructor(data=microdata,
                                                 gfactors=gf_base)
        else:
            records = tc.Records(microdata, gfactors=gf_base)
        self.base_calc = tc.Calculator(policy=tc.Policy(gf_base),
                                       records=records,
                                       verbose=self.verbose)

        # Reform calculator
        # Initialize a policy object
        gd_reform = tc.GrowDiff()
        gf_reform = tc.GrowFactors()
        if self.params["growdiff_response"]:
            gd_reform.update_growdiff(self.params["growdiff_response"])
            gd_reform.apply_to(gf_reform)
        if use_cps:
            records = tc.Records.cps_constructor(data=microdata,
                                                 gfactors=gf_reform)
        else:
            records = tc.Records(microdata, gfactors=gf_reform)
        policy = tc.Policy(gf_reform)
        policy.implement_reform(self.params['policy'])
        # Initialize Calculator
        self.reform_calc = tc.Calculator(policy=policy, records=records,
                                         verbose=self.verbose)

    def run(self, varlist=DEFAULT_VARIABLES):
        """
        Run the calculators. TaxBrain will determine whether to do a static or
        partial equilibrium run based on the user's inputs when initializing
        the TaxBrain object.
        Parameters
        ----------
        varlist: list of variables from the microdata to be stored in each year
        Returns
        -------
        None
        """
        if not isinstance(varlist, list):
            msg = f"'varlist' is of type {type(varlist)}. Must be a list."
            raise TypeError(msg)
        if self.params["behavior"]:
            if self.verbose:
                print("Running dynamic simulations")
            self._dynamic_run(varlist)
        else:
            if self.verbose:
                print("Running static simulations")
            self._static_run(varlist)

    def weighted_totals(self, var):
        """
        Create a pandas DataFrame that shows the weighted sum or a specified
        variable under the baseline policy, reform policy, and the difference
        between the two.
        Parameters
        ----------
        var: Variable you want the weighted total of.
        Returns
        -------
        A Pandas DataFrame with rows for the baseline total, reform total,
        and the difference between the two.
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
        return pd.DataFrame([base_totals, reform_totals, differences],
                            index=["Base", "Reform", "Difference"])

    def multi_var_table(self, varlist, calc):
        """
        Create a Pandas DataFrame with multiple variables from the specified
        data source
        Parameters
        ----------
        varlist: list of variables to include in the table
        calc: specify reform or base calculator data
        Returns
        -------
        A Pandas DataFrame containing the weighted sum of each variable passed
        in the `varlist` argument for each year in the analysis.
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
        return df.transpose()

    def distribution_table(self, year, groupby, income_measure, calc):
        """
        Method to create a distribution table
        Parameters
        ----------
        year: which year the distribution table data should be from
        groupby: determines how the rows in the table are sorted
            options: 'weighted_deciles', 'standard_income_bins', 'soi_agi_bin'
        income_measure: determines which variable is used to sort the rows in
                        the table
            options: 'expanded_income' or 'expanded_income_baseline'
        calc: which calculator to use: base or reform
        Returns
        -------
        DataFrame containing a distribution table
        """
        # pull desired data
        if calc.lower() == "base":
            data = self.base_data[year]
        elif calc.lower() == "reform":
            data = self.reform_data[year]
        else:
            raise ValueError("calc must be either BASE or REFORM")
        # minor data preparation before calling the function
        data["num_returns_ItemDed"] = data["s006"].where(
            data["c04470"] > 0., 0.
        )
        data["num_returns_StandardDed"] = data["s006"].where(
            data["standard"] > 0., 0.
        )
        data["num_returns_AMT"] = data["s006"].where(
            data["c09600"] > 0., 0.
        )
        if income_measure == "expanded_income_baseline":
            base_income = self.base_data[year]["expanded_income"]
            data["expanded_income_baseline"] = base_income
        table = create_distribution_table(data, groupby, income_measure)
        return table

    def differences_table(self, year, groupby, tax_to_diff):
        """
        Method to create a differences table
        Parameters
        ----------
        year: which year the difference table should be from
        groupby: determines how the rows in the table are sorted
            options: 'weighted_deciles', 'standard_income_bins', 'soi_agi_bin'
        tax_to_diff: which tax to take the difference of
            options: 'iitax', 'payrolltax', 'combined'
        run_type: use data from the static or dynamic run
        Returns
        -------
        DataFrame containing a differences table
        """
        base_data = self.base_data[year]
        reform_data = self.reform_data[year]
        table = create_difference_table(base_data, reform_data, groupby,
                                        tax_to_diff)
        return table

    # ----- private methods -----
    def _static_run(self, varlist):
        """
        Run the calculator for a static analysis
        """
        if "s006" not in varlist:  # ensure weight is always included
            varlist.append("s006")
        # Use copies of the calculators so you can run both static and
        # dynamic calculations on same TaxBrain instance
        for yr in range(self.start_year, self.end_year + 1):
            self.base_calc.advance_to_year(yr)
            self.reform_calc.advance_to_year(yr)
            # run calculations in parallel
            delay = [delayed(self.base_calc.calc_all()),
                     delayed(self.reform_calc.calc_all())]
            _ = compute(*delay)
            self.base_data[yr] = self.base_calc.dataframe(varlist)
            self.reform_data[yr] = self.reform_calc.dataframe(varlist)

    def _dynamic_run(self, varlist):
        """
        Run a dynamic response
        """
        delay_list = []
        for year in range(self.start_year, self.end_year + 1):
            delay = delayed(self._run_dynamic_calc)(self.base_calc,
                                                    self.reform_calc,
                                                    self.params["behavior"],
                                                    year, varlist)
            delay_list.append(delay)
        _ = compute(*delay_list)
        del delay_list

    def _run_dynamic_calc(self, calc1, calc2, behavior, year, varlist):
        """
        Function used to parallelize the dynamic run function

        Parameters
        ----------
        calc1: Calculator object representing the baseline policy
        calc2: Calculator object representing the reform policy
        year: year for the calculations
        """
        calc1_copy = copy.deepcopy(calc1)
        calc2_copy = copy.deepcopy(calc2)
        calc1_copy.advance_to_year(year)
        calc2_copy.advance_to_year(year)
        # use response function to capture dynamic effects
        base, reform = behresp.response(calc1_copy, calc2_copy,
                                        behavior, dump=True)
        self.base_data[year] = base[varlist]
        self.reform_data[year] = reform[varlist]
        del calc1_copy, calc2_copy, base, reform

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
