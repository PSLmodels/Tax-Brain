(Chap_Usage)=
# How to Use Tax-Brain

The Tax-Brain package is centered around the `TaxBrain` object. Any analysis
using Tax-Brain starts by importing and creating a `TaxBrain` instance.

```python
from taxbrain import TaxBrain

tb = TaxBrain(2019, 2029, use_cps=True, reform="reform.json",
              assump="assumptions.json", behavior={"sub": 0.25})
```

`TaxBrain` takes the following arguments on initialization:

1. `start_year`: First year in the analysis.
2. `end_year`: Last year in the analysis.
3. `microdata`<sup>*</sup>: Either a path to a micro-data CSV file or a Pandas
   DataFrame containing micro-data suitable for use in Tax-Calculator
4. `use_cps`<sup>*</sup>: Boolean indicator for whether to use the CPS micro-data file
   included in Tax-Calculator. If this is true, do not give a value for the
   `microdata` argument.
5. `reform`<sup>*</sup>: Individual income tax policy reform. Can either be a string
   pointing to a JSON file, the contents of a JSON file, or a dictionary.
6. `behavior`<sup>*</sup>: Individual behavioral assumptions used by the Behavioral-Responses
    package.
7. `assump`<sup>*</sup>: Economic assumptions. Can either be a string pointing to a
   JSON file, the contents of a JSON file, or a dictionary.
8. `verbose`<sup>*</sup>: Boolean indicator for whether or not to print progress updates
   as the models run. Default value is False.

<sup>*</sup> indicates optional argument

Tax-Brain will analyze these inputs to determine which models to run and for
what years. To start the models, the users can simply use the `run` method:

```python
tb.run()
```

This will create two Tax-Calculator instances - one for current law (base)
and another for the user specified policy (reform).

`run()` also takes an optional argument, `varlist`, to indicate which variables
in the micro-data the user would like saved. Pandas DataFrames containing
micro-data from the reform and base calculators are stored in the `reform_data`
and `base_data`, respectively, attributes of the `TaxBrain` instance (both
attributes are dictionaries).

The dictionaries are structured so that each year in the analysis is a key
paired to the DataFrame for that particular year:

```python
# Access the DataFrame containing data from the reform caclulator for the year 2019
tb.reform_data[2019]
# Access the DataFrame containing data from the base calculator for the year 2020
tb.base_data[2020]
```

This gives the user the option of performing a more detailed analysis of the
data or producing custom tables and graphs.
There are also multiple built in methods for producing tables:

* `weighted_totals(var)`: Produces a table with the weighted sum of the
  specified variables (`var`) for each year in the analysis under the baseline
  policy, reform policy, and the difference between the two.
* `distribution_table(year, groupby, income_measure, calc): Produces a table
  showing the distribution of a number of variables across the income spectrum.
* `differences_table(year, groupby, tax_to_diff)`: Produces a table showing the
  change in a number of variables across the income distribution.

## Stacked Reforms

TaxBrain also can produce stacked revenue estimates. To use this feature,
simply modify your reform dictionary so that each key is the name of a section
of your reform and each item is the associated reform provisions, as shown
below.

```python
payroll_json = """{"SS_Earnings_thd": {"2021": 400000}}"""
CG_rate_json = """{
   "CG_brk3": {"2021": [1000000, 1000000, 1000000, 1000000, 1000000]},
   "CG_rt4": {"2021": 0.396}
}"""
reform_dict = {
   "Payroll Threshold Increase": payroll_json,
   "Capital Gains Tax Changes": CG_rate_json
}
tb = TaxBrain(2021, 2022, reform=reform_dict, stacked=True, use_cps=True)
tb.run()
tb.stacked_table * 1e-9
```
This code will produce the following table:

|                   |2021              |2022             |2021-2022                |
|--------------------------|------------------|-----------------|-------------------------|
|Payroll Threshold Increase|65.97             |70.9             |136.87                   |
|Capital Gains Tax Changes |19.57             |18.95            |38.52                    |
|Total                     |85.54             |89.85            |175.39                   |



As more models are added, Tax-Brain's usage will change to adjust. While we
will try and maintain backwards compatibility, that obviously cannot always
happen. This document will be updated as Tax-Brain evolves.