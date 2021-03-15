# Tax-Brain Command Line Interface

The `taxbrain` package comes with a built in command line interface (CLI). With
this CLI, users can access all of `taxbrain's` modeling capabilities without
the need to code. The CLI is installed when you install the `taxbrain` conda
package.[^1] Once installed, there are a number of arguments that can be used:

* `startyear`: The first year of the analysis you want to run.
* `endyear`: The final year of the analysis you want to run.
* `--data`: The file path to a micro-dataset that is formatted for use with Tax-Calculator
* `--usecps`: If this argument is present, the CPS file that is included in Tax-Calculator will be used for the analysis
* `--reform`: Path to a JSON file containing a policy reform for the analysis.
* `--behavior`: Path to a JSON file containing the behavioral assumptions for the analysis.
* `--outdir`: Path to the directory where all of the output will be stored. If this is not specified, output will be written to the current directory.
* `--name`: Name you'd like to give the analysis.
* `--report`: If this argument is present, a PDF report analyzing the provided reform will be produced.
* `--author`: If you're creating a report, this name will be listed as the author.

## Usage

Given a JSON reform file, `reformA.json`, this is the command you would use to
run the `taxbrain` CLI for years 2020 to 2029:

```bash
taxbrain 2020 2029 --reform reformA.json
```

This output of this command will be a new directory containing the file
`aggregate_tax_liability.csv`, which shows the total individual income, payroll,
and combined tax liability for each year of the analysis. Additionally, there
will be subdirectories for each year of the analysis containing three files:
`distribution_table_base_{year}.csv`, `distribution_table_reform_{year}.csv`,
and `differences_table_{year}.csv`. The first two show the distribution of a
number of income and tax variables under the baseline and reform policies.
respectively. The Third file shows how these variables change in that year.
All of these tables are grouped by expanded income deciles.

[^1]: You can install `taxbrain` with this command: `conda install -c pslmodels taxbrain`.