import shutil
from taxbrain import cli_core
from pathlib import Path


def test_cli():
    """
    Test core logic of the CLI
    """
    startyear = 2019
    endyear = 2020
    data = "CPS"
    reform = None
    behavior = None
    assump = None
    baseline = None
    outdir = ""
    name = "test_cli"
    make_report = False
    author = None
    cli_core(
        startyear,
        endyear,
        data,
        reform,
        behavior,
        assump,
        baseline,
        outdir,
        name,
        make_report,
        author,
    )
    outpath = Path(outdir, name)
    # assert that all folders and files have been created
    assert outpath.is_dir()
    assert Path(outpath, "aggregate_tax_liability.csv").exists()
    for year in range(startyear, endyear + 1):
        yearpath = Path(outpath, str(year))
        assert yearpath.is_dir()
        assert Path(yearpath, f"distribution_table_base_{year}.csv").exists()
        assert Path(yearpath, f"distribution_table_reform_{year}.csv").exists()
        assert Path(yearpath, f"differences_table_{year}.csv").exists()
    shutil.rmtree(outpath)
