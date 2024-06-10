import os
import pytest
import pandas as pd
from taxbrain import TaxBrain


CUR_PATH = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture(scope="session")
def reform_json_str():
    reform = """
        {
            "policy": {
                "SS_thd50": {"2019": [50000, 100000, 50000, 50000, 50000]},
                "SS_thd85": {"2019": [50000, 100000, 50000, 50000, 50000]},
                "SS_Earnings_thd": {"2019": 400000},
                "FICA_ss_trt_employee": {"2020": 0.0625,
                                "2021": 0.063,
                                "2022": 0.0635,
                                "2023": 0.064,
                                "2024": 0.0645,
                                "2025": 0.065,
                                "2026": 0.0605,
                                "2027": 0.061,
                                "2028": 0.0615},
                "STD-indexed": {"2019": false}
            }
        }
    """
    return reform


@pytest.fixture(scope="session")
def assump_json_str():
    assump = """
        {
            "consumption": {"BEN_housing_value": {"2019": 0.7}},
            "growdiff_baseline": {"ABOOK": {"2019": 0.01}},
            "growdiff_response": {"ACGNS": {"2019": 0.01}}
        }
    """
    return assump


@pytest.fixture(
    scope="session",
)
def tb_static(reform_json_str):
    return TaxBrain(2018, 2019, microdata="CPS", reform=reform_json_str)


@pytest.fixture(scope="session")
def tb_dynamic(reform_json_str):
    return TaxBrain(
        2018,
        2019,
        microdata="CPS",
        reform=reform_json_str,
        behavior={"sub": 0.25},
    )


@pytest.fixture(scope="session")
def empty_mods():
    return {
        "consumption": {},
        "growdiff_response": {},
        "policy": {},
        "growdiff_baseline": {},
        "behavior": {},
    }


@pytest.fixture(scope="session")
def sample_input():
    params = {
        "params": {
            "policy": {"_FICA_ss_trt_employee": {"2019": [0.075]}},
            "behavior": {"sub": {"2019": [0.1]}},
        },
        "jsonstrs": "",
        "errors_warnings": {
            "policy": {"errors": {}, "warnings": {}},
            "behavior": {"errors": {}, "warnings": {}},
        },
        "start_year": 2019,
        "data_source": "PUF",
        "use_full_sample": False,
    }
    return params
