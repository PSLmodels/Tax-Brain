# imports
import numpy as np
import taxcalc as tc
import copy
from taxbrain import corporate_incidence


# Tests of corporate_incidence functions

"""
2. Test that shares sum to 1 in each year (distribute function)
3. Some expected tests with distribute (including cases with 100% on capital/labor, diff timing (including immediate))
"""


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
    shareholder_income_vars = ["p22250", "p23250", "e00600", "e00650"]
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
    pct = ((sum_test - sum_base) / revenue)
    assert np.allclose(pct, shares["Labor share"])
    sum_test = 0
    sum_base = 0
    for v in shareholder_income_vars:
        sum_test += (test_calc.array(v) * test_calc.array("s006")).sum()
        sum_base += (calc1.array(v) * calc1.array("s006")).sum()
    pct = ((sum_test - sum_base) / revenue)
    assert np.allclose(pct, shares["Shareholder share"])
    sum_test = 0
    sum_base = 0
    for v in other_capital_income_vars:
        sum_test += (test_calc.array(v) * test_calc.array("s006")).sum()
        sum_base += (calc1.array(v) * calc1.array("s006")).sum()
    pct = ((sum_test - sum_base) / revenue)
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
        "e00650",
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


def test_share_transition():
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
            "Labor share": 0.2,
            "Shareholder share": 0.7,
            "All capital share": 0.1,
        },
        "Long run years": 5
    }

    # Expected shares
    expected_shares = {
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
        }
    }

    # Now check shares match expectation for each year
    for year in range(2025, 2034):
        print("Checking for year ", year)
        calc1.advance_to_year(year)
        test_calc = corporate_incidence.distribute(
            copy.deepcopy(calc1),
            revenue,
            year,
            2025,
            param_updates)

        # Check that shares match expected
        sum_test = 0
        sum_base = 0
        for v in wage_income_vars:
            sum_test += (test_calc.array(v) * test_calc.array("s006")).sum()
            sum_base += (calc1.array(v) * calc1.array("s006")).sum()
        pct1 = ((sum_test - sum_base) / revenue)
        assert np.allclose(pct1, expected_shares["Labor share"][year])
        sum_test = 0
        sum_base = 0
        for v in shareholder_income_vars:
            sum_test += (test_calc.array(v) * test_calc.array("s006")).sum()
            sum_base += (calc1.array(v) * calc1.array("s006")).sum()
        pct2 = ((sum_test - sum_base) / revenue)
        assert np.allclose(pct2, expected_shares["Shareholder share"][year])
        sum_test = 0
        sum_base = 0
        for v in other_capital_income_vars:
            sum_test += (test_calc.array(v) * test_calc.array("s006")).sum()
            sum_base += (calc1.array(v) * calc1.array("s006")).sum()
        pct3 = ((sum_test - sum_base) / revenue)
        assert np.allclose(pct3, expected_shares["All capital share"][year])

        # also check that shares always sum to 1
        assert np.allclose(1.0, pct1 + pct2 + pct3)

