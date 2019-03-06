import pytest
import pandas as pd
from taxbrain import TaxBrain


def test_arg_validation():
    with pytest.raises(ValueError):
        TaxBrain(2018, 2020, microdata="../puf.csv", use_cps=True)
    with pytest.raises(AssertionError):
        TaxBrain("2018", "2020")
    with pytest.raises(AssertionError):
        TaxBrain(TaxBrain.LAST_BUDGET_YEAR, TaxBrain.FIRST_BUDGET_YEAR)
    with pytest.raises(AssertionError):
        TaxBrain(TaxBrain.FIRST_BUDGET_YEAR - 1, 2018)
    with pytest.raises(AssertionError):
        TaxBrain(2018, TaxBrain.LAST_BUDGET_YEAR + 1)


def test_static_run(tb_static):
    tb_static.run()


def test_dynamic_run(tb_dynamic):
    tb_dynamic.run({2018: {"BE_sub": 0.25}})


def test_weighted_totals(tb_static):
    table = tb_static.weighted_totals("c00100")
    assert isinstance(table, pd.DataFrame)


def test_differences_table(tb_dynamic):
    table = tb_dynamic.differences_table(2018, "weighted_deciles", "combined")
    assert isinstance(table, pd.DataFrame)


def test_distribution_table(tb_static):
    table = tb_static.distribution_table(2019, "weighted_deciles",
                                         "expanded_income", "reform")
    assert isinstance(table, pd.DataFrame)
    table = tb_static.distribution_table(2019, "weighted_deciles",
                                         "expanded_income", "base")
    assert isinstance(table, pd.DataFrame)
    with pytest.raises(ValueError):
        tb_static.distribution_table(2018, "weighted_deciles",
                                     "expanded_income", "nonreform")


def test_user_input(reform_json_str):
    valid_reform = {
        2019: {
            "_II_rt7": [0.40]
        }
    }
    # Test valid reform dictionary with No assumption
    TaxBrain(2018, 2020, use_cps=True, reform=valid_reform)
    TaxBrain(2018, 2020, use_cps=True, reform=reform_json_str)
    invalid_assump = {
        "consumption": {}
    }
    # Test valid reform and assumptions dictionary
    valid_assump = {
        "consumption": {},
        "growdiff_baseline": {},
        "growdiff_response": {}
    }
    TaxBrain(2018, 2019, use_cps=True, assump=valid_assump)
    tb = TaxBrain(2018, 2019, use_cps=True, reform=valid_reform,
                  assump=valid_assump)
    required_param_keys = {"policy", "consumption", "growdiff_baseline",
                           "growdiff_response", "behavior"}
    assert set(tb.params.keys()) == required_param_keys
    with pytest.raises(ValueError):
        TaxBrain(2018, 2020, use_cps=True, assump=invalid_assump)
    invalid_assump = {
        "consumption": {},
        "growdiff_baseline": {},
        "growdiff_response": {},
        "invalid": {}
    }
    with pytest.raises(ValueError):
        TaxBrain(2018, 2020, use_cps=True, assump=invalid_assump)
    with pytest.raises(TypeError):
        TaxBrain(2018, 2020, use_cps=True, reform=True)
    with pytest.raises(TypeError):
        TaxBrain(2018, 2020, use_cps=True, assump=True)
