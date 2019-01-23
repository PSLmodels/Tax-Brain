import pytest
import pandas as pd
from taxbrain import TaxBrain


def test_arg_validation():
    with pytest.raises(ValueError):
        TaxBrain(2018, 2020, microdata='../puf.csv', use_cps=True)
    with pytest.raises(AssertionError):
        TaxBrain('2018', '2020')
    with pytest.raises(AssertionError):
        TaxBrain(2020, 2018)
    with pytest.raises(AssertionError):
        TaxBrain(2010, 2018)
    with pytest.raises(AssertionError):
        TaxBrain(2018, 2030)


def test_static_run(tb):
    tb.static_run()


def test_dynamic_run(tb):
    tb.dynamic_run()


def test_weighted_totals(tb):
    table = tb.weighted_totals('c00100', 'static')
    assert isinstance(table, pd.DataFrame)
    table = tb.weighted_totals('c00100', 'dynamic')
    assert isinstance(table, pd.DataFrame)
    with pytest.raises(AssertionError):
        tb.weighted_totals('c00100', 'total')
