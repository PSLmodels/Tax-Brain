# imports
import copy


# Default parameters for the CorporateIncidence class
CI_PARAMS = {
    "Incidence": {  # long-run incidence of corporate tax
        "Labor share": 0.5,
        "Shareholder share": 0.4,
        "All capital share": 0.1,
    },
    "Long run years": 10,  # number of years to reach long-run incidence
}

VAR_NAME_MAP = {
    "Dividends": "e00650",
    "Capital gains": "e01100",
    "Self-employment income": "e00900",
    "Taxable interest": "e00300",
    "Tax-exempt interest": "e00300",
}

SHORT_RUN_SHARES = {
    "Labor share": 0.0,
    "Shareholder share": 1.0,
    "All capital share": 0.0,
}


# TODO: think about if corp revenue intended to be entered in billions or what
def distribute(calc, corp_revenue, year, start_year, param_updates=None):
    """
    Function that distributes the corporate income tax incidence across
    individual income tax payers.
    """
    if param_updates:
        CI_PARAMS.update(param_updates)
    # Make a copy so as not to modify calculator object
    calc_corp = copy.deepcopy(calc)
    # Find index of year working on
    i = year - start_year
    # take revenue total for the relevant year
    if isinstance(corp_revenue, dict):
        corp_revenue = corp_revenue["year"]
    else:
        corp_revenue = corp_revenue[i]
    # adjust parameters for the transition to the long run
    shares = {}
    for k, v in CI_PARAMS["Incidence"].items():
        if CI_PARAMS["Long run years"] == 0:
            shares[k] = v
        else:
            increment = (v - SHORT_RUN_SHARES[k]) / CI_PARAMS["Long run years"]
            # use min() so don't "overshoot" the long run share
            shares[k] = (
                SHORT_RUN_SHARES[k]
                + min(i, CI_PARAMS["Long run years"]) * increment
            )

    # update income in the calc object
    calc_corp = _update_income(calc_corp, corp_revenue, shares)

    return calc_corp


def _update_income(calc, revenue, shares):
    """
    Implement income changes to account for corporate tax
    incidence on household filers
    """
    # Find aggregate change in wages
    agg_wage = shares["Labor share"] * revenue
    # Find aggregate change in dividend/capital gains
    agg_shareholder = shares["Shareholder share"] * revenue
    # Find aggregate change in other capital income
    agg_other_capital = shares["All capital share"] * revenue
    # With aggregates, compute pct change in each
    wage_income_vars = ["e00200"]
    shareholder_income_vars = ["p22250", "p23250", "e00600"]
    other_capital_income_vars = [
        "e00300",
        "e00400",
        "e01100",
        "e01200",
        "e02000",
    ]  # do we try to capture just some of e02000?
    denom = 0
    for v in wage_income_vars:
        denom += (calc.array(v) * calc.array("s006")).sum()
    pct_change_wage = agg_wage / denom
    denom = 0
    for v in shareholder_income_vars:
        denom += (calc.array(v) * calc.array("s006")).sum()
    pct_change_shareholder = agg_shareholder / denom
    denom = 0
    for v in other_capital_income_vars:
        denom += (calc.array(v) * calc.array("s006")).sum()
    pct_change_other_capital = agg_other_capital / denom

    # we will apply these percentage changes to the relevant income sources
    # need to scale other wages so their sum equals total
    for v in wage_income_vars + ["e00200p", "e00200s"]:
        delta = calc.array(v) * pct_change_wage
        calc.incarray(v, delta)
    for v in shareholder_income_vars:
        delta = calc.array(v) * pct_change_shareholder
        calc.incarray(v, delta)
    for v in other_capital_income_vars + ["e00650"]:
        # scale qualified dividends as well, though they are included
        # in e00600
        delta = calc.array(v) * pct_change_other_capital
        calc.incarray(v, delta)

    return calc
