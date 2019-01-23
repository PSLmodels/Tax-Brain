from taxbrain import TaxBrain

reform_url = "https://raw.githubusercontent.com/PSLmodels/Tax-Calculator/b6c09ecc8c59850647f00e42097b57d594e1ce94/taxcalc/reforms/2017_law.json"
tb = TaxBrain(2018, 2027, use_cps=True, reform=reform_url)
# run static analysis
tb.static_run()
static_table = tb.weighted_totals('c00100', 'static')
print('Tax Liability by Year')
print('Static Results')
print(static_table)

# run dynamic analysis
tb.dynamic_run({2018: {"BE_sub": 0.25}})
dynamic_table = tb.weighted_totals('c00100', 'dynamic')
print('Dynamic Results')
print(dynamic_table)
