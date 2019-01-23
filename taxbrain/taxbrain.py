import copy
import taxcalc as tc
import pandas as pd
from taxcalc.utils import DIST_VARIABLES
from behresp import response
from dask import compute, delayed


class TaxBrain:

    FIRST_BUDGET_YEAR = tc.Policy.JSON_START_YEAR
    LAST_BUDGET_YEAR = tc.Policy.LAST_BUDGET_YEAR

    def __init__(self, start_year, end_year, microdata='puf.csv',
                 use_cps=False, reform=None, assump=None, verbose=False):
        """
        Constructor for the TaxBrain class
        Parameters
        ----------
        microdata: Either a Pandas DataFrame or path to the PUF
        policy: individual income tax policy. Can be either a string
        behavior: behavioral assumptions
        verbose: specifies whether or not to write progress in stdout
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

    def static_run(self, varlist=DIST_VARIABLES):
        """
        Run the calculator
        """
        if "s006" not in varlist:  # ensure weight is always included
            varlist.append("s006")
        if self.verbose:
            print("Running static simulations")
        # Use copies of the calculators so you can run both static and
        # dynamic calculations on same TaxBrain instance
        base_calc = copy.deepcopy(self.base_calc)
        reform_calc = copy.deepcopy(self.reform_calc)
        for yr in range(self.start_year, self.end_year + 1):
            base_calc.advance_to_year(yr)
            reform_calc.advance_to_year(yr)
            # run calculations in parallel
            delay = [delayed(base_calc.calc_all()),
                     delayed(reform_calc.calc_all())]
            _ = compute(*delay)
            self.base_data[yr]["static"] = base_calc.dataframe(varlist)
            self.reform_data[yr]["static"] = reform_calc.dataframe(varlist)

        del base_calc, reform_calc

    def dynamic_run(self, behavior):
        """
        Run a dynamic response
        """
        if self.verbose:
            print("Running dynamic simulations")

        delay_list = []
        for year in range(self.start_year, self.end_year + 1):
            delay = delayed(self._run_dynamic_calc)(self.base_calc,
                                                    self.reform_calc,
                                                    behavior,
                                                    year)
            delay_list.append(delay)
        _ = compute(*delay_list)
        del delay_list

    def weighted_totals(self, var, run_type):
        assert run_type == "static" or run_type == "dynamic", (
            "run_type must be either 'static' or 'dynamic'"
        )
        base_totals = {}
        reform_totals = {}
        differences = {}
        for year in range(self.start_year, self.end_year + 1):
            base_totals[year] = (self.base_data[year][run_type]["s006"] *
                                 self.base_data[year][run_type][var]).sum()
            reform_totals[year] = (self.reform_data[year][run_type]["s006"] *
                                   self.reform_data[year][run_type][var]).sum()
            differences[year] = reform_totals[year] - base_totals[year]
        return pd.DataFrame([base_totals, reform_totals, differences],
                            index=["Base", "Reform", "Difference"])

    # ----- private methods -----
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
        self.base_data[year]["dynamic"] = base
        self.reform_data[year]["dynamic"] = reform
        del calc1_copy, calc2_copy
