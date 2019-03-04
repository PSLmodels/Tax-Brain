import time
from taxbrain import TaxBrain

start = time.time()
reform_url = "https://raw.githubusercontent.com/PSLmodels/Tax-Calculator/master/taxcalc/reforms/Larson2019.json"
tb = TaxBrain(2018, 2027, use_cps=True, reform=reform_url)
load_time = time.time() - start
# run static analysis
static_start = time.time()
tb.run()
static_table = tb.weighted_totals("c00100")
print("Tax Liability by Year\n")
print("Static Results")
print(static_table)
static_time = time.time() - static_start

# run dynamic analysis
tb2 = TaxBrain(2018, 2027, use_cps=True, reform=reform_url,
               behavior={2018: {"BE_sub": 0.25}})
dynamic_start = time.time()
tb2.run()
dynamic_table = tb2.weighted_totals("c00100")
print("Dynamic Results")
print(dynamic_table)
dynamic_time = time.time() - dynamic_start

# produce a differences table
diff_start = time.time()
diff = tb.differences_table(2019, "weighted_deciles", "combined")
print("\nDifferences Table for 2019")
print(diff)
diff_time = time.time() - diff_start

# produce a distribution table
dist_start = time.time()
dist = tb.distribution_table(2019, "weighted_deciles", "expanded_income",
                             "reform")
print("\nDistribution Table for 2019")
print(dist)
dist_time = time.time() - dist_start
run_time = time.time() - start

# print diagnostics
print("Time Diagnostics (Seconds)")
print(f"Total time: {run_time}")
print(f"Load Time: {load_time}")
print(f"Static Run Time: {static_time}")
print(f"Dynamic Run Time: {dynamic_time}")
print(f"Differences Table Time: {diff_time}")
print(f"Diagnostics Table Time: {dist_time}")
