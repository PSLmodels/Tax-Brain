import pytest
from taxbrain import TaxBrain


@pytest.fixture(scope="session")
def tb():
    return TaxBrain(2018, 2019, use_cps=True)
