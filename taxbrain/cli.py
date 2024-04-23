"""
Command line interface for the Tax-Brain package
"""

import argparse
from taxbrain import TaxBrain, report
from pathlib import Path
from datetime import datetime


def make_tables(tb, year, outpath):
    """
    Make and write all of the tables for a given year

    Parameters
    ----------
    tb: TaxBrain object
        instance of a TaxBrain object
    year: int
        year to produce tables for
    outpath: str
        path to save output to

    Returns
    -------
    None
        tables saved to disk
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
    diff_table = tb.differences_table(year, "weighted_deciles", "combined")
    diff_table.to_csv(Path(outpath, f"differences_table_{year}.csv"))
    del dist_table_base, dist_table_reform, diff_table


def cli_core(
    startyear,
    endyear,
    data,
    usecps,
    reform,
    behavior,
    assump,
    baseline,
    outdir,
    name,
    make_report,
    author,
):
    """
    Core logic for the CLI

    Parameters
    ----------
    startyear: int
        year to start analysis
    endyear: int
        last year for analysis
    data: str or Pandas DataFrame
        path to or DataFrame with data for Tax-Calculator
    usecps: bool
        whether to use the CPS or (if False) the PUF-based file
    reform: dict
        parameter changes for reform run in Tax-Calculator
    behavior: dict
        behavioral assumptions for Behavioral-Responses
    assump: dict
        consumption assumptions
    base_policy: dict
        parameter changes (relative to current law baseline) for baseline
        policy
    verbose: bool
        indicator for printing of output

    Returns
    -------
    None
        reports saved to disk at path specified by outdir
    """
    tb = TaxBrain(
        start_year=startyear,
        end_year=endyear,
        microdata=data,
        use_cps=usecps,
        reform=reform,
        behavior=behavior,
        assump=assump,
        base_policy=baseline,
        verbose=True,
    )
    tb.run()

    # create outputs
    dirname = name
    if not dirname:
        dirname = f"TaxBrain Analysis {datetime.today().date()}"
    outputpath = Path(outdir, dirname)
    outputpath.mkdir(exist_ok=True)
    # create output tables
    aggregate = tb.weighted_totals("combined")
    aggregate.to_csv(Path(outputpath, "aggregate_tax_liability.csv"))
    for year in range(startyear, endyear + 1):
        yeardir = Path(outputpath, str(year))
        yeardir.mkdir(exist_ok=True)
        make_tables(tb, year, yeardir)

    if make_report:
        report(tb, name=name, outdir=outputpath, author=author)


def cli_main():
    """
    Command line interface to taxbrain package

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    parser_description = (
        "This is the command line interface for the taxbrain package."
    )
    parser = argparse.ArgumentParser(
        prog="taxbrain", description=parser_description
    )
    parser.add_argument(
        "startyear",
        help=("startyear is the first year of the analysis you want to run."),
        default=TaxBrain.FIRST_BUDGET_YEAR,
        type=int,
    )
    parser.add_argument(
        "endyear",
        help=("endyear is the last year of the analysis you want to run."),
        default=TaxBrain.LAST_BUDGET_YEAR,
        type=int,
    )
    parser.add_argument(
        "--data",
        help=(
            "The file path to a micro-dataset that is formatted for use in "
            "Tax-Calculator."
        ),
        default=None,
    )
    parser.add_argument(
        "--usecps",
        help=(
            "If this argument is present, the CPS file included in "
            "Tax-Calculator will be used for the analysis."
        ),
        default=False,
        action="store_true",
    ),
    parser.add_argument(
        "--reform",
        help=("--reform should be a path to a JSON file."),
        default=None,
    )
    parser.add_argument(
        "--behavior",
        help=(
            "--behavior should be a path to a JSON file containing behavioral "
            "assumptions."
        ),
        default=None,
    )
    parser.add_argument(
        "--assump",
        help=(
            "--assump should be a path to a JSON file containing user "
            "specified economic assumptions."
        ),
        default=None,
    )
    parser.add_argument(
        "--baseline",
        help=(
            "--baseline should be a path to a JSON file containing a policy "
            "that will be used as the baseline of the analysis"
        ),
    )
    parser.add_argument(
        "--outdir",
        help=(
            "outdir is the name of the output directory. Not including "
            "--outdir will result in files being written to the current "
            "directory."
        ),
        default="",
    ),
    parser.add_argument(
        "--name",
        help=(
            "Name of the analysis. This will be used to name the directory "
            "where all output files will be written."
        ),
        default=None,
    )
    parser.add_argument(
        "--report",
        help=(
            "including --report will trigger the creation of a PDF report "
            "summarizing the effects of the tax policy being modeled."
        ),
        action="store_true",
    )
    parser.add_argument(
        "--author",
        help=(
            "If you are creating a report, this the name that will be listed "
            "as the author"
        ),
    )
    args = parser.parse_args()

    # run the analysis
    cli_core(
        args.startyear,
        args.endyear,
        args.data,
        args.usecps,
        args.reform,
        args.behavior,
        args.assump,
        args.baseline,
        args.outdir,
        args.name,
        args.report,
    )


if __name__ == "__main__":
    cli_main()
