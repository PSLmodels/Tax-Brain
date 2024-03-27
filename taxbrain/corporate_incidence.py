# imports
import copy


class CorporateIncidence:

    # Default parameters for the CorporateIncidence class
    CI_PARAMS = {
        "Normal returns": {
             "Dividends": 0.4,
             "Capital gains": 0.4,
             "Self-employment income": 0.4,
             #TODO: check if taxdata has other breakouts for ordinary income
             "Taxable interest": 1.0,
             "Tax-exempt interest": 1.0,
        },
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

    def __init__(self, calc, corp_revenue, year, start_year, param_updates=None):
        if param_updates:
            self.CI_PARAMS.update(param_updates)
        self.calc = copy.deepcopy(calc)
        self.year = year
        # Find index of year
        i = year - start_year
        # take revenue total for the relevant year
        if type(corp_revenue) == dict:
             self.corp_revenue = corp_revenue["year"]
        else:
            self.corp_revenue = corp_revenue[i]
        # adjust parameters for the transition to the long run
        if self.CI_PARAMS["Long run years"] == 0:
             factor = 1.0
        else:
             factor = max(i / self.CI_PARAMS["Long run years"], 1.0)
        self.shares = {}
        for k, v in self.CI_PARAMS["Incidence"]:
            self.shares[v] =

    def calculate_corporate_incidence(self):
        # take revenue total for the relevant year
        revenue = self.corp_revenue[self.year]  #NOTE: for now, assume revenue is a dictionary, but we might want to allow for a list or np.array (will just need to think through indexing in those cases)

        # using a linear transition, find the incidence rates
        # note that initial year 100% of the tax is borne by shareholders


        # update income in the calc object
        calc_corp = self._update_income(self, )


    def _update_income(self, revenue, params):
            """
            Implement income changes to account for corporate tax
            incidence on household filers
            """
            # compute AGI minus itemized deductions, agi_m_ided
            agi = calc.array('c00100')
            ided = np.where(calc.array('c04470') < calc.array('standard'),
                            0., calc.array('c04470'))
            agi_m_ided = agi - ided
            # assume behv response only for filing units with positive agi_m_ided
            pos = np.array(agi_m_ided > 0., dtype=bool)
            delta_income = np.where(pos, taxinc_change, 0.)
            # allocate delta_income into three parts
            # pylint: disable=unsupported-assignment-operation
            winc = calc.array('e00200')
            delta_winc = np.zeros_like(agi)
            delta_winc[pos] = delta_income[pos] * winc[pos] / agi_m_ided[pos]
            oinc = agi - winc
            delta_oinc = np.zeros_like(agi)
            delta_oinc[pos] = delta_income[pos] * oinc[pos] / agi_m_ided[pos]
            delta_ided = np.zeros_like(agi)
            delta_ided[pos] = delta_income[pos] * ided[pos] / agi_m_ided[pos]
            # confirm that the three parts are consistent with delta_income
            assert np.allclose(delta_income, delta_winc + delta_oinc - delta_ided)
            # add the three parts to different records variables embedded in calc
            calc.incarray('e00200', delta_winc)
            calc.incarray('e00200p', delta_winc)
            calc.incarray('e00300', delta_oinc)
            calc.incarray('e19200', delta_ided)
            return calc
