import copy

from compdevkit import FunctionsTest

from compconfig import functions, helpers


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
            ],
            "EITC_c": [{"EIC": "0kids", "year": 2019, "value": 1000.0}],
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
            ],
            "ACTC_c": [{"year": 2019, "value": 2000.0}],
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


def test_convert_adj():
    adj = {
        "STD": [
            {"MARS": "single", "year": 2019, "value": 0},
            {"MARS": "mjoint", "year": 2019, "value": 1},
            {"MARS": "mjoint", "year": 2022, "value": 10}
        ],
        "CPI_offset": [
            {"year": 2019, "value": -0.001}
        ],
        "EITC_c": [{"EIC": "0kids", "year": 2019, "value": 1000.0}],
        "BEN_ssi_repeal": [
            {"year": 2019, "data_source": "CPS", "value": True}
        ]
    }

    res = helpers.convert_adj(adj, 2019)

    assert res == {
        "STD": {
            2019: [0, 1, 12268.8, 18403.2, 24537.6],
            2022: [0, 10, 13081.03, 19621.54, 26162.06]
        },
        "CPI_offset": {
            2019: -0.001
        },
        "EITC_c": {
            2019: [1000.0, 3529.87, 5829.75, 6558.98]
        },
        "BEN_ssi_repeal": {
            2019: True
        }
    }

def test_convert_adj_w_index():
    adj = {
        "ACTC_c": [
            {"year": 2019, "value": 2000.0},
            {"year": 2026, "value": 1000.0}
        ],
        "STD": [
            {"year": 2019, "MARS": "single", "value": 2000.0},
            {"year": 2020, "MARS": "mjoint", "value": 12345},
            {"year": 2026, "MARS": "single", "value": 1000.0}
        ],
        "STD_checkbox": [{"value": False}]
    }
    res = helpers.convert_adj(adj, 2019)
    assert res == {
        "STD-indexed": {
            2019: False
        },
        "ACTC_c": {2019: 2000.0, 2026: 1000.0},
        "STD": {
            2019: [2000.0, 24537.6, 12268.8, 18403.2, 24537.6],
            2020: [2000.0, 12345, 12268.8, 18403.2, 24537.6],
            2026: [1000.0, 12345.0, 12268.8, 18403.2, 24537.6]
        }
    }