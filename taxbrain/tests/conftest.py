import pytest
from taxbrain import TaxBrain


@pytest.fixture(scope="session")
def reform_json_str():
    reform = """
        {
            "policy": {
                "_SS_thd50": {"2019": [[50000, 100000, 50000, 50000, 50000]]},
                "_SS_thd85": {"2019": [[50000, 100000, 50000, 50000, 50000]]},
                "_SS_Earnings_thd": {"2019": [400000]},
                "_FICA_ss_trt": {"2020": [0.125],
                                 "2021": [0.126],
                                 "2022": [0.127],
                                 "2023": [0.128],
                                 "2024": [0.129],
                                 "2025": [0.130],
                                 "2026": [0.131],
                                 "2027": [0.132],
                                 "2028": [0.133]}
            }
        }
    """
    return reform


@pytest.fixture(scope="session")
def assump_json_str():
    assump = """
        {
            "consumption": {"_BEN_housing_value": {"2019": [0.7]}},
            "growdiff_baseline": {"_ABOOK": {"2019": [0.01]}},
            "growdiff_response": {"_ACGNC": {"2019": [0.01]}}
        }
    """
    return assump


@pytest.fixture(scope="session",)
def tb_static(reform_json_str):
    return TaxBrain(2018, 2019, use_cps=True, reform=reform_json_str)


@pytest.fixture(scope="session")
def tb_dynamic(reform_json_str):
    return TaxBrain(2018, 2019, use_cps=True, reform=reform_json_str,
                    behavior={2018: {"BE_sub": 0.25}})


@pytest.fixture(scope="session")
def empty_mods():
    return {"consumption": {}, "growdiff_response": {}, "policy": {},
            "growdiff_baseline": {}, "behavior": {}}
