import pytest
from taxbrain import TaxBrain


@pytest.fixture(scope="session")
def tb():
    return TaxBrain(2018, 2019, use_cps=True)


@pytest.fixture(scope="session")
def empty_mods():
    return {"consumption": {}, "growdiff_response": {}, "policy": {},
            "growdiff_baseline": {}, "behavior": {}}
