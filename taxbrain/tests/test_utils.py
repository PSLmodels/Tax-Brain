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
    # testing using RGB tuples for the colors
    fig = taxbrain.volcano_plot(
        tb_static, 2019,
        increase_color=(0.1, 0.2, 0.5), decrease_color=(0.2, 0.2, 0.5)
    )


def test_lorenz_curve(tb_static):
    fig = taxbrain.lorenz_curve(tb_static, 2019)


def test_revenue_plot(tb_static):
    fig = taxbrain.revenue_plot(tb_static)
    with pytest.raises(ValueError):
        taxbrain.revenue_plot(tb_static, tax_vars=["income", "combined"])
    with pytest.raises(AssertionError):
        taxbrain.revenue_plot(tb_static, tax_vars=[])
