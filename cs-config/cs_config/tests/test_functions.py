from cs_kit import CoreTestFunctions
from cs_config import functions


OK_ADJUSTMENT = {
    "policy": {
        "STD": [
            {"MARS": "single", "year": 2019, "value": 0},
            {"MARS": "mjoint", "year": 2019, "value": 1},
            {"MARS": "mjoint", "year": 2022, "value": 10},
        ],
        "parameter_indexing_CPI_offset": [{"year": 2019, "value": -0.001}],
        "EITC_c": [{"EIC": "0kids", "year": 2019, "value": 1000.0}],
    },
    "behavior": {"inc": [{"value": -0.1}]},
}


BAD_ADJUSTMENT = {
    "policy": {
        "STD": [
            {"MARS": "single", "year": 2019, "value": -10},
            {"MARS": "mjoint", "year": 2019, "value": 1},
            {"MARS": "mjoint", "year": 2022, "value": 10},
        ],
        "parameter_indexing_CPI_offset": [{"year": 2019, "value": -0.001}],
        "ACTC_c": [{"year": 2019, "value": 2000.0}],
    },
    "behavior": {"sub": [{"value": -0.1}]},
}

EMPTY_ADJUSTMENT = {"policy": {}, "behavior": {}}


CHECKBOX_ADJUSTMENT = {
    "policy": {
        "STD": [
            {"MARS": "single", "year": 2019, "value": 10},
            {"MARS": "mjoint", "year": 2019, "value": 1},
            {"MARS": "mjoint", "year": 2022, "value": 10},
        ],
        "STD_checkbox": [{"value": False}],
    },
    "behavior": {},
}


def test_start_year_with_data_source():
    """
    Test interaction between PUF and CPS data sources and the start year.
    """
    data = functions.get_inputs({"data_source": "PUF"})
    assert data["meta_parameters"]["year"]["validators"]["choice"]["choices"][0] == 2013
    data = functions.get_inputs({"data_source": "CPS"})
    assert data["meta_parameters"]["year"]["validators"]["choice"]["choices"][0] == 2014

    ew = {
        "policy": {"errors": {}, "warnings": {}},
        "behavior": {"errors": {}, "warnings": {}},
    }
    res = functions.validate_inputs(
        {"data_source": "CPS", "year": 2013}, {"policy": {}, "behavior": {}}, ew
    )
    assert res["errors_warnings"]["policy"]["errors"].get("year")


class TestFunctions1(CoreTestFunctions):
    get_version = functions.get_version
    get_inputs = functions.get_inputs
    validate_inputs = functions.validate_inputs
    run_model = functions.run_model
    ok_adjustment = OK_ADJUSTMENT
    bad_adjustment = BAD_ADJUSTMENT


class TestFunctions2(CoreTestFunctions):
    get_version = functions.get_version
    get_inputs = functions.get_inputs
    validate_inputs = functions.validate_inputs
    run_model = functions.run_model
    ok_adjustment = CHECKBOX_ADJUSTMENT
    bad_adjustment = BAD_ADJUSTMENT


class TestFunctions3(CoreTestFunctions):
    get_version = functions.get_version
    get_inputs = functions.get_inputs
    validate_inputs = functions.validate_inputs
    run_model = functions.run_model
    ok_adjustment = EMPTY_ADJUSTMENT
    bad_adjustment = BAD_ADJUSTMENT
