# imports
import numpy as np
import pandas as pd
import taxcalc as tc
import copy
import pytest
from taxbrain import corporate_incidence


# Tests of corporate_incidence functions


def test_update_income_shares():
    """
    Test of the _update_income() function
    """
    # create a calculator object
    rec = tc.Records.cps_constructor()
    pol = tc.Policy()
    calc1 = tc.Calculator(policy=pol, records=rec)

    # set a corp revenue amount
    revenue = 100_000_000_00.0

    # set shares
    shares = {
        "Labor share": 0.2,
        "Shareholder share": 0.7,
        "All capital share": 0.1,
    }
    # use update income function
    test_calc = corporate_incidence._update_income(
        copy.deepcopy(calc1), revenue, shares
    )

    wage_income_vars = ["e00200"]
    shareholder_income_vars = ["p22250", "p23250", "e00600"]
    other_capital_income_vars = [
        "e00300",
        "e00400",
        "e01100",
        "e01200",
        "e02000",
    ]

    # Check that shares match expected
    sum_test = 0
    sum_base = 0
    for v in wage_income_vars:
        sum_test += (test_calc.array(v) * test_calc.array("s006")).sum()
        sum_base += (calc1.array(v) * calc1.array("s006")).sum()
    pct = (sum_test - sum_base) / revenue
    assert np.allclose(pct, shares["Labor share"])
    sum_test = 0
    sum_base = 0
    for v in shareholder_income_vars:
        sum_test += (test_calc.array(v) * test_calc.array("s006")).sum()
        sum_base += (calc1.array(v) * calc1.array("s006")).sum()
    pct = (sum_test - sum_base) / revenue
    assert np.allclose(pct, shares["Shareholder share"])
    sum_test = 0
    sum_base = 0
    for v in other_capital_income_vars:
        sum_test += (test_calc.array(v) * test_calc.array("s006")).sum()
        sum_base += (calc1.array(v) * calc1.array("s006")).sum()
    pct = (sum_test - sum_base) / revenue
    assert np.allclose(pct, shares["All capital share"])


def test_update_income_totals():
    """
    Test of the _update_income() function
    """
    # create a calculator object
    rec = tc.Records.cps_constructor()
    pol = tc.Policy()
    calc1 = tc.Calculator(policy=pol, records=rec)

    # set a corp revenue amount
    revenue = 100_000_000_00.0

    # set shares
    shares = {
        "Labor share": 0.2,
        "Shareholder share": 0.7,
        "All capital share": 0.1,
    }
    # use update income function
    test_calc = corporate_incidence._update_income(
        copy.deepcopy(calc1), revenue, shares
    )

    income_vars = [
        "e00200",
        "p22250",
        "p23250",
        "e00600",
        "e00300",
        "e00400",
        "e01100",
        "e01200",
        "e02000",
    ]
    # check that in total, amount of income change equals revenue
    sum_test = 0
    sum_base = 0
    for v in income_vars:
        sum_test += (test_calc.array(v) * test_calc.array("s006")).sum()
        sum_base += (calc1.array(v) * calc1.array("s006")).sum()
    diff = sum_test - sum_base
    assert np.allclose(revenue, diff)


expected_shares5 = {
    "Labor share": {
        2025: 0.0,
        2026: 0.04,
        2027: 0.08,
        2028: 0.12,
        2029: 0.16,
        2030: 0.2,
        2031: 0.2,
        2032: 0.2,
        2033: 0.2,
    },
    "Shareholder share": {
        2025: 1.0,
        2026: 0.94,
        2027: 0.88,
        2028: 0.82,
        2029: 0.76,
        2030: 0.7,
        2031: 0.7,
        2032: 0.7,
        2033: 0.7,
    },
    "All capital share": {
        2025: 0.0,
        2026: 0.02,
        2027: 0.04,
        2028: 0.06,
        2029: 0.08,
        2030: 0.1,
        2031: 0.1,
        2032: 0.1,
        2033: 0.1,
    },
}
expected_shares0 = {
    "Labor share": {
        2025: 0.2,
        2026: 0.2,
        2027: 0.2,
        2028: 0.2,
    },
    "Shareholder share": {
        2025: 0.7,
        2026: 0.7,
        2027: 0.7,
        2028: 0.7,
    },
    "All capital share": {
        2025: 0.1,
        2026: 0.1,
        2027: 0.1,
        2028: 0.1,
    },
}
expected_shares1 = {
    "Labor share": {
        2025: 0.0,
        2026: 0.2,
        2027: 0.2,
        2028: 0.2,
    },
    "Shareholder share": {
        2025: 1.0,
        2026: 0.7,
        2027: 0.7,
        2028: 0.7,
    },
    "All capital share": {
        2025: 0.0,
        2026: 0.1,
        2027: 0.1,
        2028: 0.1,
    },
}


@pytest.mark.parametrize(
    "transition_years,end_year,expected_shares",
    [
        (5, 2033, expected_shares5),
        (0, 2028, expected_shares0),
        (1, 2028, expected_shares1),
    ],
    ids=["5 years", "immediate", "1 year"],
)
def test_share_transition(transition_years, end_year, expected_shares):
    """
    Test the transition of share over time in the
    corp_incidence_distribute function.
    """
    # create a calculator object
    rec = tc.Records.cps_constructor()
    pol = tc.Policy()
    calc1 = tc.Calculator(policy=pol, records=rec)

    # set a corp revenue amount
    revenue = [100_000_000_00.0] * (2034 - 2025)

    # Define different income sources
    # TODO: should make these constants in corp_incidence.py
    wage_income_vars = ["e00200"]
    shareholder_income_vars = ["p22250", "p23250", "e00600"]
    other_capital_income_vars = [
        "e00300",
        "e00400",
        "e01100",
        "e01200",
        "e02000",
    ]
    # Long run shares
    param_updates = {
        "Incidence": {
            "Labor share": 0.2,
            "Shareholder share": 0.7,
            "All capital share": 0.1,
        },
        "Long run years": transition_years,
    }

    # Now check shares match expectation for each year
    for year in range(2025, end_year + 1):
        print("Checking for year ", year)
        calc1.advance_to_year(year)
        test_calc = corporate_incidence.distribute(
            copy.deepcopy(calc1), revenue, year, 2025, param_updates
        )

        # Check that shares match expected
        sum_test = 0
        sum_base = 0
        for v in wage_income_vars:
            sum_test += (test_calc.array(v) * test_calc.array("s006")).sum()
            sum_base += (calc1.array(v) * calc1.array("s006")).sum()
        pct1 = (sum_test - sum_base) / revenue
        assert np.allclose(pct1, expected_shares["Labor share"][year])
        sum_test = 0
        sum_base = 0
        for v in shareholder_income_vars:
            sum_test += (test_calc.array(v) * test_calc.array("s006")).sum()
            sum_base += (calc1.array(v) * calc1.array("s006")).sum()
        pct2 = (sum_test - sum_base) / revenue
        assert np.allclose(pct2, expected_shares["Shareholder share"][year])
        sum_test = 0
        sum_base = 0
        for v in other_capital_income_vars:
            sum_test += (test_calc.array(v) * test_calc.array("s006")).sum()
            sum_base += (calc1.array(v) * calc1.array("s006")).sum()
        pct3 = (sum_test - sum_base) / revenue
        assert np.allclose(pct3, expected_shares["All capital share"][year])

        # also check that shares always sum to 1
        assert np.allclose(1.0, pct1 + pct2 + pct3)


# Validation check
# Try to use same parameters and recreate TPC
# (https://www.taxpolicycenter.org/sites/default/files/alfresco/publication-pdfs/412651-How-TPC-Distributes-the-Corporate-Income-Tax.PDF)
# Table 8, with percent of burden by income quantile
def test_validation():
    """
    Test the transition of share over time in the
    corp_incidence_distribute function.
    """
    # create a calculator object
    rec = tc.Records.cps_constructor()
    pol = tc.Policy()
    calc1 = tc.Calculator(policy=pol, records=rec)

    # set a corp revenue amount
    revenue = [100_000_000_00.0] * (2034 - 2025)

    # Define different income sources
    # TODO: should make these constants in corp_incidence.py
    wage_income_vars = ["e00200"]
    shareholder_income_vars = ["p22250", "p23250", "e00600", "e00650"]
    other_capital_income_vars = [
        "e00300",
        "e00400",
        "e01100",
        "e01200",
        "e02000",
    ]
    # Long run shares
    param_updates = {
        "Incidence": {
            "Labor share": 0.0,
            "Shareholder share": 1.0,
            "All capital share": 0.0,
        },
        "Long run years": 0,
    }

    # expected shares if full burden on shareholders:
    expected = pd.DataFrame(
        data=[
            0.000031,
            0.0,
            0.001008,
            0.003991,
            0.003974,
            0.008655,
            0.013243,
            0.020796,
            0.027376,
            0.052368,
            0.077858,
            0.790699,
            1,
            0.074559,
            0.122593,
            0.593546,
        ],
        index=[
            "0-10n",
            "0-10z",
            "0-10p",
            "10-20",
            "20-30",
            "30-40",
            "40-50",
            "50-60",
            "60-70",
            "70-80",
            "80-90",
            "90-100",
            "ALL",
            "90-95",
            "95-99",
            "Top 1%",
        ],
    )

    test_calc = corporate_incidence.distribute(
        copy.deepcopy(calc1), revenue, 2025, 2025, param_updates
    )
    calc1.advance_to_year(2025)
    test_calc.advance_to_year(2025)
    print("Calc current year = ", calc1.current_year)
    print("Test Calc current year = ", test_calc.current_year)
    calc1.calc_all()
    test_calc.calc_all()
    dt1, dt2 = calc1.distribution_tables(test_calc, "weighted_deciles")
    print("Distribution table: ")
    total_income_change = (
        dt2.loc["ALL", "expanded_income"] - dt1.loc["ALL", "expanded_income"]
    )
    print("total income change = ", total_income_change)
    pct_change_income = (
        dt2["expanded_income"] - dt1["expanded_income"]
    ) / total_income_change
    print(np.array(pct_change_income.values))
    print(expected[0].values)

    assert np.allclose(
        np.array(pct_change_income.values), expected[0].values, atol=1e-5
    )
