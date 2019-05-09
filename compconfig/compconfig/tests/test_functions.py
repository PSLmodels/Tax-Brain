import copy

from compdevkit import FunctionsTest

from compconfig import functions


def test_functions():
    # test your functions with FunctionsTest here
    adj_good = {
        "policy": {
            "STD": [
                {"MARS": "single", "year": 2019, "value": 0},
                {"MARS": "mjoint", "year": 2019, "value": 1},
                {"MARS": "mjoint", "year": 2022, "value": 10}
            ],
            "CPI_offset": [
                {"year": 2019, "value": -0.001}
            ]
        },
        "behavior": {
            "inc": [
                {"value": -0.1}
            ]
        }
    }

    adj_bad = {
        "policy": {
            "STD": [
                {"MARS": "single", "year": 2019, "value": -10},
                {"MARS": "mjoint", "year": 2019, "value": 1},
                {"MARS": "mjoint", "year": 2022, "value": 10}
            ],
            "CPI_offset": [
                {"year": 2019, "value": -0.001}
            ]
        },
        "behavior": {
            "sub": [
                {"value": -0.1}
            ]
        }
    }
    ta = FunctionsTest(
        get_inputs=functions.get_inputs,
        validate_inputs=functions.validate_inputs,
        run_model=functions.run_model,
        ok_adjustment=adj_good,
        bad_adjustment=adj_bad
    )
    ta.test()


def test_checkbox_params():
    adj = {
        "policy": {
            "STD": [
                {"MARS": "single", "year": 2019, "value": 10},
                {"MARS": "mjoint", "year": 2019, "value": 1},
                {"MARS": "mjoint", "year": 2022, "value": 10}
            ],
            "STD_checkbox": [{"value": False}]
        },
        "behavior": {}
    }
    errors_warnings = {
        "policy": {"errors": {}, "warnings": {}},
        "behavior": {"errors": {}, "warnings": {}}
    }
    assert functions.validate_inputs({}, copy.deepcopy(adj), errors_warnings)

    assert functions.run_model({"use_full_sample": False, "data_source": "CPS"}, adj)
