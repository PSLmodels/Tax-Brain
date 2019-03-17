# Tax-Brain

Tax-Brain provides a one-stop-shop for tax policy analysis by serving as an
interface for multiple tax models. The user specifies a policy reform, economic
or behavioral assumptions, some data, and Tax-Brain takes care of the rest.

Tax-Brain handles any interaction between the models it wraps and makes it easy
for the user to access data and build tables and graphs.

Tax-Brain is centered around the `TaxBrain` object. This object has a number of
inputs to allow the user to conduct their specific analysis:

* `start_year`: First year of the analysis.
* `end_year`: Last year in the analysis
* `microdata`: Either a Pandas DataFrame containing micro-data or a path to a
  file containing micro-data.
* `use_cps`: A boolean value indicated whether to use the CPS file included
  in Tax-Calculator.
* `reform`: A JSON file or dictionary in the style used by Tax-Calculator
  containing an individual income or payroll tax policy reform.
* `behavior`: Individual behavior assumptions as used by the Behavior-Response
  model.
* `assump`: A JSON file or dictionary containing economic assumptions as used
  by Tax-Calculator.
* `verbose`: A boolean indicator indicated whether or not to write progress
  report messages as the models run.

Once the `TaxBrain` object has been initialized, all the user needs to do is
use the `run()` method and everything else is handled internally. BY analyzing
the user's inputs, `TaxBrain` determines if it should run a static or dynamic
analysis, which years to run the analysis for, and which data to save as the
models run.

After the models have run, the user has easy access to the saved data and can
create their own graphs and tables, or use the built in methods to create them.
