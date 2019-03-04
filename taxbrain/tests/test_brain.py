import pytest
import pandas as pd
from taxbrain import TaxBrain


def test_arg_validation():
    with pytest.raises(ValueError):
        TaxBrain(2018, 2020, microdata="../puf.csv", use_cps=True)
    with pytest.raises(AssertionError):
        TaxBrain("2018", "2020")
    with pytest.raises(AssertionError):
        TaxBrain(2020, 2018)
    with pytest.raises(AssertionError):
        TaxBrain(2010, 2018)
    with pytest.raises(AssertionError):
        TaxBrain(2018, 2030)


def test_static_run(tb_static):
    tb_static.run()


def test_dynamic_run(tb_dynamic):
    tb_dynamic.run({2018: {"BE_sub": 0.25}})


def test_weighted_totals(tb_static):
    table = tb_static.weighted_totals("c00100")
    assert isinstance(table, pd.DataFrame)


def test_differences_table(tb_dynamic):
    table = tb_dynamic.differences_table(2018, "weighted_deciles", "combined")
    assert isinstance(table, pd.DataFrame)


def test_distribution_table(tb_static):
    table = tb_static.distribution_table(2019, "weighted_deciles",
                                         "expanded_income", "reform")
    assert isinstance(table, pd.DataFrame)
    table = tb_static.distribution_table(2019, "weighted_deciles",
                                         "expanded_income", "base")
    assert isinstance(table, pd.DataFrame)
    with pytest.raises(ValueError):
        tb_static.distribution_table(2018, "weighted_deciles",
                                     "expanded_income", "nonreform")
