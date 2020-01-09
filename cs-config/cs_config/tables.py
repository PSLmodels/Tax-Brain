"""
Functions to create the tables displayed in COMP
"""
from .constants import AGG_ROW_NAMES
from taxbrain import TaxBrain


def summary_aggregate(res, tb):
    """
    Function to produce aggregate revenue tables
    """
    if not isinstance(res, dict):
        raise TypeError(
            f"'res' is of type {type(res)}. Must be dictionary object."
        )
    if not isinstance(tb, TaxBrain):
        raise TypeError(
            f"'tb' is of type {type(tb)}. Must be TaxBrain object"
        )
    # tax totals for baseline
    tax_vars = ["iitax", "payrolltax", "combined"]
    aggr_base = tb.multi_var_table(tax_vars, "base")
    aggr_base.index = AGG_ROW_NAMES
    # tax totals for reform
    aggr_reform = tb.multi_var_table(tax_vars, "reform")
    aggr_reform.index = AGG_ROW_NAMES
    # tax difference
    aggr_d = aggr_reform - aggr_base
    # add to dictionary
    res["aggr_d"] = (aggr_d / 1e9).round(3)
    res["aggr_1"] = (aggr_base / 1e9).round(3)
    res["aggr_2"] = (aggr_reform / 1e9).round(3)
    del aggr_base, aggr_reform, aggr_d
    return res


def summary_dist_xbin(res, tb, year):
    """
    res is dictionary of summary-results DataFrames.
    df1 contains results variables for baseline policy.
    df2 contains results variables for reform policy.
    returns augmented dictionary of summary-results DataFrames.
    """
    if not isinstance(res, dict):
        raise TypeError(
            f"'res' is of type {type(res)}. Must be dictionary object."
        )
    if not isinstance(tb, TaxBrain):
        raise TypeError(
            f"'tb' is of type {type(tb)}. Must be TaxBrain object"
        )
    if not isinstance(year, int):
        raise TypeError(
            f"'year' is of type {type(year)}. Must be an integer"
        )
    # create distribution tables grouped by xbin
    # baseline distribution table
    res["dist1_xbin"] = tb.distribution_table(year, "standard_income_bins",
                                              "expanded_income", "base")
    # reform distribution table
    # ensure income is grouped on the same measure
    expanded_income_baseline = tb.base_data[year]["expanded_income"]
    tb.reform_data[year]["expanded_income_baseline"] = expanded_income_baseline
    res["dist2_xbin"] = tb.distribution_table(year, "standard_income_bins",
                                              "expanded_income_baseline",
                                              "reform")
    del tb.reform_data[year]["expanded_income_baseline"]
    return res


def summary_diff_xbin(res, tb, year):
    """
    res is dictionary of summary-results DataFrames.
    df1 contains results variables for baseline policy.
    df2 contains results variables for reform policy.
    returns augmented dictionary of summary-results DataFrames.
    """
    if not isinstance(res, dict):
        raise TypeError(
            f"'res' is of type {type(res)}. Must be dictionary object."
        )
    if not isinstance(tb, TaxBrain):
        raise TypeError(
            f"'tb' is of type {type(tb)}. Must be TaxBrain object"
        )
    if not isinstance(year, int):
        raise TypeError(
            f"'year' is of type {type(year)}. Must be an integer"
        )
    # create difference tables grouped by xbin
    res["diff_itax_xbin"] = tb.differences_table(year, "standard_income_bins",
                                                 "iitax")
    res["diff_ptax_xbin"] = tb.differences_table(year, "standard_income_bins",
                                                 "payrolltax")
    res["diff_comb_xbin"] = tb.differences_table(year, "standard_income_bins",
                                                 "combined")
    return res


def summary_dist_xdec(res, tb, year):
    """
    res is dictionary of summary-results DataFrames.
    df1 contains results variables for baseline policy.
    df2 contains results variables for reform policy.
    returns augmented dictionary of summary-results DataFrames.
    """
    if not isinstance(res, dict):
        raise TypeError(
            f"'res' is of type {type(res)}. Must be dictionary object."
        )
    if not isinstance(tb, TaxBrain):
        raise TypeError(
            f"'tb' is of type {type(tb)}. Must be TaxBrain object"
        )
    if not isinstance(year, int):
        raise TypeError(
            f"'year' is of type {type(year)}. Must be an integer"
        )
    # create distribution tables grouped by xdec
    res["dist1_xdec"] = tb.distribution_table(year, "weighted_deciles",
                                              "expanded_income", "base")
    # reform distribution table
    # ensure income is grouped on the same measure
    expanded_income_baseline = tb.base_data[year]["expanded_income"]
    tb.reform_data[year]["expanded_income_baseline"] = expanded_income_baseline
    res["dist2_xdec"] = tb.distribution_table(year, "weighted_deciles",
                                              "expanded_income_baseline",
                                              "reform")
    del tb.reform_data[year]["expanded_income_baseline"]
    return res


def summary_diff_xdec(res, tb, year):
    """
    res is dictionary of summary-results DataFrames.
    df1 contains results variables for baseline policy.
    df2 contains results variables for reform policy.
    returns augmented dictionary of summary-results DataFrames.
    """
    if not isinstance(res, dict):
        raise TypeError(
            f"'res' is of type {type(res)}. Must be dictionary object."
        )
    if not isinstance(tb, TaxBrain):
        raise TypeError(
            f"'tb' is of type {type(tb)}. Must be TaxBrain object"
        )
    if not isinstance(year, int):
        raise TypeError(
            f"'year' is of type {type(year)}. Must be an integer"
        )
    # create difference tables grouped by xdec
    res["diff_itax_xdec"] = tb.differences_table(year, "weighted_deciles",
                                                 "iitax")
    res["diff_ptax_xdec"] = tb.differences_table(year, "weighted_deciles",
                                                 "payrolltax")
    res["diff_comb_xdec"] = tb.differences_table(year, "weighted_deciles",
                                                 "combined")
    return res
