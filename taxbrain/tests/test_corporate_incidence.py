# imports
import numpy as np
import taxcalc as tc
import copy
from taxbrain import corporate_incidence


# Tests of corporate_incidence functions

"""
1. Test that update income results in an aggregate change in income equal to the corp tax revenue change
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

    # should we test an individual obs?

    # Check that shares match expected
    sum_test = 0
    sum_base = 0
    for v in wage_income_vars:
        sum_test += (test_calc.array(v) * test_calc.array("s006")).sum()
        sum_base += (calc1.array(v) * calc1.array("s006")).sum()
        pct = (sum_test / revenue) - 1
        assert np.allclose(pct, shares["Labor share"])
    sum_test = 0
    sum_base = 0
    for v in shareholder_income_vars:
        sum_test += (test_calc.array(v) * test_calc.array("s006")).sum()
        sum_base += (calc1.array(v) * calc1.array("s006")).sum()
        pct = (sum_test / revenue) - 1
        assert np.allclose(pct, shares["Shareholder share"])
    sum_test = 0
    sum_base = 0
    for v in other_capital_income_vars:
        sum_test += (test_calc.array(v) * test_calc.array("s006")).sum()
        sum_base += (calc1.array(v) * calc1.array("s006")).sum()
        pct = (sum_test / revenue) - 1
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
    test_calc = corporate_incidence._update_income(calc1, revenue, shares)

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
        print(
            "diff in arrays = ",
            np.absolute(test_calc.array(v) - calc1.array(v)).max(),
        )
    diff = sum_test - sum_base
    assert np.allclose(revenue, diff)
