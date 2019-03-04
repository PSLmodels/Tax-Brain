import copy
import taxcalc as tc
import pandas as pd
from taxcalc.utils import (DIST_VARIABLES, DIFF_VARIABLES,
                           create_distribution_table, create_difference_table)
from behresp import response
from dask import compute, delayed


class TaxBrain:

    FIRST_BUDGET_YEAR = tc.Policy.JSON_START_YEAR
    LAST_BUDGET_YEAR = tc.Policy.LAST_BUDGET_YEAR
    # Default list of variables saved for each year
    DEFAULT_VARIABLES = list(set(DIST_VARIABLES).union(set(DIFF_VARIABLES)))

    def __init__(self, start_year, end_year, microdata='puf.csv',
                 use_cps=False, reform=None, behavior=None, assump=None,
                 verbose=False):
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
        if use_cps and microdata != "puf.csv":
            raise ValueError("Specified a data file with both microdata and "
                             "use_cps=True; you can only specify one.")
        assert isinstance(start_year, int) & isinstance(end_year, int), (
            "Start and end years must be integers"
        )
        assert start_year <= end_year, (f"Specified end year, {end_year}, is "
                                        "before specified start year,"
                                        f"{start_year}.")
        assert TaxBrain.FIRST_BUDGET_YEAR <= start_year, (
            f"Specified start_year, {start_year}, comes before first known "
            f"budget year, {TaxBrain.FIRST_BUDGET_YEAR}."
        )
        assert end_year <= TaxBrain.LAST_BUDGET_YEAR, (
            f"Specified end_year, {end_year}, comes after last known "
            f"budget year, {TaxBrain.LAST_BUDGET_YEAR}."
        )
        self.start_year = start_year
        self.end_year = end_year
        self.base_data = {yr: {} for yr in range(start_year, end_year + 1)}
        self.reform_data = {yr: {} for yr in range(start_year, end_year + 1)}
        self.behavior = behavior
        self.verbose = verbose

        # Create two microsimulation calculators
        # Baseline calculator
        if use_cps:
            records = tc.Records.cps_constructor()
        else:
            records = tc.Records(microdata)
        self.base_calc = tc.Calculator(policy=tc.Policy(), records=records,
                                       verbose=self.verbose)

        # Reform calculator
        # Initialize a policy object
        self.params = tc.Calculator.read_json_param_objects(reform, assump)
        policy = tc.Policy()
        policy.implement_reform(self.params['policy'])
        # Initialize Calculator
        self.reform_calc = tc.Calculator(policy=policy, records=records,
                                         verbose=self.verbose)

    def run(self, varlist=DEFAULT_VARIABLES):
        if self.behavior:
            if self.verbose:
                print("Running dynamic simulations")
            self._dynamic_run()
        else:
            if self.verbose:
                print("Running static simulations")
            self._static_run(varlist)

    def weighted_totals(self, var):
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

    def _dynamic_run(self):
        """
        Run a dynamic response
        """
        delay_list = []
        for year in range(self.start_year, self.end_year + 1):
            delay = delayed(self._run_dynamic_calc)(self.base_calc,
                                                    self.reform_calc,
                                                    self.behavior,
                                                    year)
            delay_list.append(delay)
        _ = compute(*delay_list)
        del delay_list

    def _run_dynamic_calc(self, calc1, calc2, behavior, year):
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
        base, reform = response(calc1_copy, calc2_copy,
                                behavior, self.verbose)
        self.base_data[year] = base
        self.reform_data[year] = reform
        del calc1_copy, calc2_copy
