import shutil
from pathlib import Path
from taxbrain import report


def test_report(tb_static):
    """
    Ensure that all report files are created
    """
    outdir = "testreform"
    name = "Test Report"
    report(tb_static, name=name, outdir=outdir)
    dir_path = Path(outdir)
    assert dir_path.exists()
    assert Path(dir_path, "Test-Report.md").exists()
    assert Path(dir_path, "Test-Report.pdf").exists()
    diff_png = Path(dir_path, "difference_graph.png")
    assert diff_png.exists()
    dist_png = Path(dir_path, "dist_graph.png")
    assert dist_png.exists()
    shutil.rmtree(dir_path)
    # test clean report
    _content = report(tb_static, name=name, outdir=outdir, clean=True)
    assert not dir_path.exists()
