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
        get_inputs=functions.get_defaults,
        validate_inputs=functions.validate_input,
        run_model=functions.run_model,
        ok_adjustment=adj_good,
        bad_adjustment=adj_bad
    )
    ta.test()
