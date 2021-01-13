import taxbrain
import pytest


def test_distribution_plot(tb_static):
    fig = taxbrain.distribution_plot(tb_static, 2019)


def test_differences_plot(tb_static):
    fig = taxbrain.differences_plot(tb_static, "combined")
    with pytest.raises(AssertionError):
        taxbrain.differences_plot(tb_static, "wages")


def test_volcano_plot(tb_static):
    fig = taxbrain.volcano_plot(tb_static, 2019)
    with pytest.raises(ValueError):
        taxbrain.volcano_plot(tb_static, 2019, min_y=-10000)
    fig = taxbrain.volcano_plot(tb_static, 2019, min_y=-1000, log_scale=False)
