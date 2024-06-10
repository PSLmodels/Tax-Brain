import os
import pytest
import pandas as pd
import numpy as np
from taxbrain import TaxBrain


def test_arg_validation():
    with pytest.raises(AssertionError):
        TaxBrain("2018", "2020", microdata="CPS")
    with pytest.raises(AssertionError):
        TaxBrain(
            TaxBrain.LAST_BUDGET_YEAR,
            TaxBrain.FIRST_BUDGET_YEAR,
            microdata="CPS",
        )
    with pytest.raises(AssertionError):
        TaxBrain(TaxBrain.FIRST_BUDGET_YEAR - 1, 2018, microdata="CPS")
    with pytest.raises(AssertionError):
        TaxBrain(2018, TaxBrain.LAST_BUDGET_YEAR + 1, microdata="CPS")


def test_static_run(tb_static):
    with pytest.raises(TypeError):
        tb_static.run(dict())
    tb_static.run()


def test_baseline_policy():
    base = {"II_em": {2019: 0}}
    reform = {"II_em": {2025: 2000}}

    tb = TaxBrain(2018, 2019, microdata="CPS", reform=reform, base_policy=base)
    tb.run()


@pytest.mark.requires_pufcsv
def test_baseline_policy_PUF():
    base = {"II_em": {2019: 0}}
    reform = {"II_em": {2025: 2000}}

    tb = TaxBrain(2018, 2019, microdata="PUF", reform=reform, base_policy=base)
    tb.run()


@pytest.mark.requires_tmdcsv
def test_baseline_policy_TMD():
    base = {"II_em": {2021: 0}}
    reform = {"II_em": {2025: 2000}}

    tb = TaxBrain(2021, 2022, microdata="TMD", reform=reform, base_policy=base)
    tb.run()


def test_run_corporate_distribution():
    """
    Tests the taxbrain.run method with the distribution of corporate
    income tax revenue.
    """
    base = {"II_em": {2019: 0}}
    reform = {"II_em": {2025: 2000}}
    corp_revenue = [1_000_000_000, 2_000_000_000]
    tb = TaxBrain(
        2018,
        2019,
        microdata="CPS",
        reform=reform,
        base_policy=base,
        corp_revenue=corp_revenue,
    )
    tb.run()


def test_dynamic_run_corporate_distribution():
    """
    Tests the taxbrain.run method with the distribution of corporate
    income tax revenue.
    """
    base = {"II_em": {2019: 0}}
    reform = {"II_em": {2025: 2000}}
    corp_revenue = [1_000_000_000, 2_000_000_000]
    tb = TaxBrain(
        2018,
        2019,
        microdata="CPS",
        reform=reform,
        base_policy=base,
        behavior={"sub": 0.25},
        corp_revenue=corp_revenue,
    )
    tb.run()


def test_dynamic_run(tb_dynamic):
    tb_dynamic.run()


def test_stacked_run():
    # reforms to use
    payroll_json = """{"SS_Earnings_thd": {"2021": 400000}}"""
    CG_rate_json = """{
        "CG_brk3": {"2021": [1000000, 1000000, 1000000, 1000000, 1000000]},
        "CG_rt4": {"2021": 0.396}
    }"""
    reform_dict = {
        "Payroll Threshold Increase": payroll_json,
        "Capital Gains Tax Changes": CG_rate_json,
    }
    tb = TaxBrain(
        2021, 2022, reform=reform_dict, stacked=True, microdata="CPS"
    )
    tb.run()
    # check that there is a stacked table now
    assert isinstance(tb.stacked_table, pd.DataFrame)


def test_stacked_run_corporate():
    # reforms to use
    payroll_json = """{"SS_Earnings_thd": {"2021": 400000}}"""
    CG_rate_json = """{
        "CG_brk3": {"2021": [1000000, 1000000, 1000000, 1000000, 1000000]},
        "CG_rt4": {"2021": 0.396}
    }"""
    reform_dict = {
        "Payroll Threshold Increase": payroll_json,
        "Capital Gains Tax Changes": CG_rate_json,
    }
    tb = TaxBrain(
        2021,
        2022,
        reform=reform_dict,
        stacked=True,
        microdata="CPS",
        corp_revenue=[100_000_000, 100_000_000],
    )
    tb.run()
    # check that there is a stacked table now
    assert isinstance(tb.stacked_table, pd.DataFrame)


def test_weighted_totals(tb_static):
    table = tb_static.weighted_totals("combined")
    assert isinstance(table, pd.DataFrame)
    # table.to_csv("expected_weighted_table.csv")
    cur_path = os.path.dirname(os.path.abspath(__file__))
    expected_table = pd.read_csv(
        os.path.join(cur_path, "expected_weighted_table.csv"), index_col=0
    )
    # convert columns to integers to avoid a meaningless error
    expected_table.columns = [int(col) for col in expected_table.columns]
    diffs = False
    for col in table.columns:
        if not np.allclose(table[col], expected_table[col]):
            diffs = True
    if diffs:
        new_file_name = "actual_weighted_table.csv"
        table.to_csv(os.path.join(cur_path, new_file_name))
        msg = (
            "Weighted table results differ from expected. New results are"
            " in actual_weighted_table.csv. If new results are ok, copy"
            " actual_weighted_table.csv to expected_weighted_table.csv"
            " and rerun test."
        )
        raise ValueError(msg)


def test_multi_var_table(tb_dynamic):
    with pytest.raises(ValueError):
        tb_dynamic.multi_var_table(["iitax"], "calc")
    with pytest.raises(TypeError):
        tb_dynamic.multi_var_table(set(), "base")
    table = tb_dynamic.multi_var_table(
        ["iitax", "payrolltax", "combined"], "reform"
    )
    assert isinstance(table, pd.DataFrame)


def test_differences_table(tb_dynamic):
    table = tb_dynamic.differences_table(2018, "weighted_deciles", "combined")
    assert isinstance(table, pd.DataFrame)


def test_distribution_table(tb_static):
    tb_static.run()
    table = tb_static.distribution_table(
        2019, "weighted_deciles", "expanded_income_baseline", "reform"
    )
    assert isinstance(table, pd.DataFrame)
    table = tb_static.distribution_table(
        2019, "weighted_deciles", "expanded_income", "base"
    )
    assert isinstance(table, pd.DataFrame)
    with pytest.raises(ValueError):
        tb_static.distribution_table(
            2018, "weighted_deciles", "expanded_income", "nonreform"
        )


def test_user_input(reform_json_str, assump_json_str):
    valid_reform = {"II_rt7": {2019: 0.40}}
    # Test valid reform dictionary with No assumption
    TaxBrain(2018, 2020, microdata="CPS", reform=valid_reform)
    TaxBrain(2018, 2020, microdata="CPS", reform=reform_json_str)
    invalid_assump = {"consumption": {}}
    # Test valid reform and assumptions dictionary
    valid_assump = {
        "consumption": {},
        "growdiff_baseline": {},
        "growdiff_response": {},
    }
    TaxBrain(2018, 2019, microdata="CPS", assump=valid_assump)
    TaxBrain(
        2018,
        2019,
        microdata="CPS",
        reform=reform_json_str,
        assump=assump_json_str,
    )
    tb = TaxBrain(
        2018, 2019, microdata="CPS", reform=valid_reform, assump=valid_assump
    )
    required_param_keys = {
        "policy",
        "consumption",
        "growdiff_baseline",
        "growdiff_response",
        "behavior",
        "base_policy",
    }
    assert set(tb.params.keys()) == required_param_keys
    with pytest.raises(ValueError):
        TaxBrain(2018, 2020, microdata="CPS", assump=invalid_assump)
    invalid_assump = {
        "consumption": {},
        "growdiff_baseline": {},
        "growdiff_response": {},
        "invalid": {},
    }
    with pytest.raises(ValueError):
        TaxBrain(2018, 2020, microdata="CPS", assump=invalid_assump)
    with pytest.raises(TypeError):
        TaxBrain(2018, 2020, microdata="CPS", reform=True)
    with pytest.raises(TypeError):
        TaxBrain(2018, 2020, microdata="CPS", assump=True)
