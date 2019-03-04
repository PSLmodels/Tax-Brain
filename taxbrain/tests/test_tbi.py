import pytest
from taxbrain.tbi import run_nth_year_taxcalc_model, run_tbi_model


def test_nth_year_model(empty_mods):
    """
    Test calling of the run_nth_year_taxcalc_model function
    """
    with pytest.raises(ValueError):
        run_nth_year_taxcalc_model(-10, 2017, "PUF", True, empty_mods)
    with pytest.raises(ValueError):
        run_nth_year_taxcalc_model(10, 2010, "PUF", True, empty_mods)
    with pytest.raises(ValueError):
        run_nth_year_taxcalc_model(10, 2013, "CPS", True, empty_mods)
    with pytest.raises(ValueError):
        run_nth_year_taxcalc_model(15, 2019, "PUF", True, empty_mods)
    run_nth_year_taxcalc_model(1, 2018, "CPS", False, empty_mods)


def test_tbi_model(empty_mods):
    """
    Test the run_tbi_model function
    """
    results = run_tbi_model(2018, "CPS", False, empty_mods)
    assert results.keys() == set(["outputs", "aggr_outputs"])
    assert len(results["outputs"]) == 10
    for i, result in enumerate(results["outputs"]):
        if not isinstance(results, dict):
            msg = (f"output result at index {i} is of type {type(result)}, ",
                   "not dict")
            raise TypeError(msg)

    assert len(results["aggr_outputs"]) == 3
    for i, result in enumerate(results["aggr_outputs"]):
        if not isinstance(result, dict):
            msg = (f"aggr_outputs result at index {i} is of type ",
                   "{type(result}, not dict")
            raise TypeError(msg)
