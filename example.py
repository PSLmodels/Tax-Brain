from taxbrain import TaxBrain, report


reform_url = "https://raw.githubusercontent.com/PSLmodels/Tax-Calculator/master/taxcalc/reforms/Larson2019.json"

# run static analysis

tb_static = TaxBrain(2019, 2028, use_cps=True, reform=reform_url)
tb_static.run()
static_table = tb_static.weighted_totals("c00100")
print("Tax Liability by Year\n")
print("Static Results")
print(static_table)

# run dynamic analysis

tb_dynamic = TaxBrain(
    2019, 2028, use_cps=True, reform=reform_url, behavior={"sub": 0.25}
)
tb_dynamic.run()
dynamic_table = tb_dynamic.weighted_totals("c00100")
print("Dynamic Results")
print(dynamic_table)

# produce a differences table

diff = tb_static.differences_table(2019, "weighted_deciles", "combined")
print("\nDifferences Table for 2019")
print(diff)

# produce a distribution table

dist = tb_dynamic.distribution_table(
    2019, "weighted_deciles", "expanded_income", "reform"
)
print("\nDistribution Table for 2019")
print(dist)

# produce a pdf report summarizing the effects of the reform
outdir = "larsonreform"
name = "The Social Security 2100 Act: Rep. John Larson"
author = "Anderson Frailey"
report(tb_dynamic, name=name, author=author, outdir=outdir)
