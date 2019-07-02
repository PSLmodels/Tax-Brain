"""
Command line interface for the Tax-Brain package
"""
import argparse
from taxbrain import TaxBrain
from pathlib import Path
from datetime import datetime


def make_tables(tb, year, outpath):
    """
    Make and write all of the tables for a given year
    """
    dist_table_base = tb.distribution_table(
        year, "weighted_deciles", "expanded_income", "base"
    )
    dist_table_base.to_csv(
        Path(outpath, f"distribution_table_base_{year}.csv")
    )
    dist_table_reform = tb.distribution_table(
        year, "weighted_deciles", "expanded_income", "reform"
    )
    dist_table_reform.to_csv(
        Path(outpath, f"distribution_table_reform_{year}.csv")
    )
    diff_table = tb.differences_table(
        year, "weighted_deciles", "combined"
    )
    diff_table.to_csv(
        Path(outpath, f"differences_table_{year}.csv")
    )
    del dist_table_base, dist_table_reform, diff_table


def cli_core(startyear, endyear, data, usecps, reform, behavior, assump,
             baseline, outdir, name):
    """
    Core logic for the CLI
    """
    tb = TaxBrain(
        start_year=startyear, end_year=endyear, microdata=data,
        use_cps=usecps, reform=reform, behavior=behavior,
        assump=assump, base_policy=baseline, verbose=True
    )
    tb.run()

    # create outputs
    dirname = name
    if not dirname:
        dirname = f"TaxBrain Analysis {datetime.today().date()}"
    outputpath = Path(outdir, dirname)
    outputpath.mkdir()
    # create output tables
    aggregate = tb.weighted_totals("combined")
    aggregate.to_csv(
        Path(outputpath, "aggregate_tax_liability.csv")
    )
    for year in range(startyear, endyear + 1):
        yeardir = Path(outputpath, str(year))
        yeardir.mkdir()
        make_tables(tb, year, yeardir)


def cli_main():
    """
    Command line interface to taxbrain package
    """
    parser_desription = (
        "This is the command line interface for the taxbrain package."
    )
    parser = argparse.ArgumentParser(
        prog="taxbrain",
        description=parser_desription
    )
    parser.add_argument(
        "startyear",
        help=(
            "startyear is the first year of the analysis you want to run."
        ),
        default=TaxBrain.FIRST_BUDGET_YEAR,
        type=int
    )
    parser.add_argument(
        "endyear",
        help=(
            "endyear is the last year of the analysis you want to run."
        ),
        default=TaxBrain.LAST_BUDGET_YEAR,
        type=int
    )
    parser.add_argument(
        "--data",
        help=(
            "The file path to a micro-dataset that is formatted for use in "
            "Tax-Calculator."
        ),
        default=None
    )
    parser.add_argument(
        "--usecps",
        help=(
            "If this argument is present, the CPS file included in "
            "Tax-Calculator will be used for the analysis."
        ),
        default=False,
        action="store_true"
    ),
    parser.add_argument(
        "--reform",
        help=(
            "--reform should be a path to a JSON file."
        ),
        default=None
    )
    parser.add_argument(
        "--behavior",
        help=(
            "--behavior should be a path to a JSON file containing behavioral "
            "assumptions."
        ),
        default=None
    )
    parser.add_argument(
        "--assump",
        help=(
            "--assump should be a path to a JSON file containing user "
            "specified economic assumptions."
        ),
        default=None
    )
    parser.add_argument(
        "--baseline",
        help=(
            "--baseline should be a path to a JSON file containing a policy "
            "that will be used as the baseline of the analysis"
        )
    )
    parser.add_argument(
        "--outdir",
        help=(
            "outdir is the name of the output directory. Not including "
            "--outdir will result in files being written to the current "
            "directory."
        ),
        default=""
    ),
    parser.add_argument(
        "--name",
        help=(
            "Name of the analysis. This will be used to name the directory "
            "where all output files will be written."
        ),
        default=None
    )
    args = parser.parse_args()

    # run the analysis
    cli_core(
        args.startyear, args.endyear, args.data, args.usecps, args.reform,
        args.behavior, args.assump, args.baseline, args.outdir, args.name
    )


if __name__ == "__main__":
    cli_main()
