"""
Helper functions for the various taxbrain modules
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.ticker as ticker
from collections import defaultdict
from typing import Union

import taxcalc as tc
from .typing import ParamToolsAdjustment, TaxcalcReform


def weighted_sum(df, var, wt="s006"):
    """
    Return the weighted sum of specified variable
    """
    return (df[var] * df[wt]).sum()


def distribution_plot(tb, year, figsize=(6, 4), title=True):
    """
    Create a horizontal bar chart to display the distributional change in
    after tax income
    """
    def find_percs(data, group):
        """
        Find the percentage of people in the data set that saw
        their income change by the given percentages
        """
        pop = data["s006"].sum()
        large_pos_chng = data["s006"][data["pct_change"] > 5].sum() / pop
        small_pos_chng = data["s006"][(data["pct_change"] <= 5) &
                                      (data["pct_change"] > 1)].sum() / pop
        small_chng = data["s006"][(data["pct_change"] <= 1) &
                                  (data["pct_change"] >= -1)].sum() / pop
        small_neg_change = data["s006"][(data["pct_change"] < -1) &
                                        (data["pct_change"] > -5)].sum() / pop
        large_neg_change = data["s006"][data["pct_change"] < -5].sum() / pop

        return (
            large_pos_chng, small_pos_chng, small_chng, small_neg_change,
            large_neg_change
        )

    # extract needed data from the TaxBrain object
    ati_data = pd.DataFrame(
        {"base": tb.base_data[year]["aftertax_income"],
         "reform": tb.reform_data[year]["aftertax_income"],
         "s006": tb.base_data[year]["s006"]}
    )
    ati_data["diff"] = ati_data["reform"] - ati_data["base"]
    ati_data["pct_change"] = (ati_data["diff"] / ati_data["base"]) * 100
    ati_data = ati_data.fillna(0.)  # fill in NaNs for graphing
    # group tupules: (low income, high income, income group name)
    groups = [
        (-9e99, 9e99, "All"),
        (1e6, 9e99, "$1M or More"),
        (500000, 1e6, "$500K-1M"),
        (200000, 500000, "$200K-500K"),
        (100000, 200000, "$100K-200K"),
        (75000, 100000, "$75K-100K"),
        (50000, 75000, "$50K-75K"),
        (40000, 50000, "$40K-50K"),
        (30000, 40000, "$30K-40K"),
        (20000, 30000, "$20K-30K"),
        (10000, 20000, "$10K-20K"),
        (-9e99, 10000, "Less than $10K")
    ]

    plot_data = defaultdict(list)
    # traverse list in reverse to get the axis of the plot in correct order
    for low, high, grp in groups:
        # find income changes by group
        sub_data = ati_data[(ati_data["base"] <= high) &
                            (ati_data["base"] > low)]
        results = find_percs(sub_data, grp)
        plot_data[grp] = results

    legend_labels = [
        "Increase of > 5%", "Increase 1-5%", "Change < 1%",
        "Decrease of 1-5%", "Decrease > 5%"
    ]
    labels = list(plot_data.keys())
    data = np.array(list(plot_data.values()))
    data_cumsum = data.cumsum(axis=1)
    category_colors = plt.get_cmap("GnBu")(
        np.linspace(0.15, 0.85, data.shape[1]))

    fig, ax = plt.subplots(figsize=figsize)
    ax.invert_yaxis()
    ax.set_xlim(0, np.sum(data, axis=1).max())

    for i, (colname, color) in enumerate(zip(legend_labels, category_colors)):
        widths = data[:, i]
        starts = data_cumsum[:, i] - widths
        ax.barh(labels, widths, left=starts, height=0.9,
                label=colname, color=color)
        # add text label
        xcenters = starts + widths / 2
        r, g, b, _ = color
        text_color = "white" if r * g * b < 0.5 else "darkgrey"
        for y, (x, c) in enumerate(zip(xcenters, widths)):
            ax.text(x, y, f"{c * 100:.1f}%", ha="center", va="center",
                    color=text_color)
    ax.legend(bbox_to_anchor=(1, 1), loc="upper left", fontsize="small")
    ax.set_xlabel("Portion of Bin", fontweight="bold")
    ax.set_ylabel("Expanded Income Bin", fontweight="bold")
    ax.get_xaxis().set_major_formatter(
        mpl.ticker.FuncFormatter(lambda x, p: format(f'{int(x * 100)}%'))
    )
    if title:
        title = f"Percentage Change In After Tax Income - {year}"
        ax.set_title(title, fontweight='bold')
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", which="both", length=0, pad=15)

    return fig


def differences_plot(tb, tax_type, figsize=(6, 4), title=True):
    """
    Create a bar chart that shows the change in total liability for a given
    tax
    """
    acceptable_taxes = ["income", "payroll", "combined"]
    msg = f"tax_type must be one of the following: {acceptable_taxes}"
    assert tax_type in acceptable_taxes, msg

    # find change in each tax variable
    tax_vars = ["iitax", "payrolltax", "combined"]
    agg_base = tb.multi_var_table(tax_vars, "base")
    agg_reform = tb.multi_var_table(tax_vars, "reform")
    agg_diff = agg_reform - agg_base

    # transpose agg_diff to make plotting easier
    plot_data = agg_diff.transpose()
    tax_var = tax_vars[acceptable_taxes.index(tax_type)]
    plot_data["color"] = np.where(plot_data[tax_var] < 0, "red", "blue")
    fig, ax = plt.subplots(figsize=figsize)
    ax.grid(True, axis='y', alpha=0.55)
    ax.set_axisbelow(True)
    ax.bar(
        plot_data.index, plot_data["combined"], alpha=0.55,
        color=plot_data["color"]
    )
    if title:
        ax.set_title(f"Change in Aggregate {tax_type.title()} Tax Liability")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.get_yaxis().set_major_formatter(
        mpl.ticker.FuncFormatter(lambda x, p: format(f"${int(x / 1e9):,}b"))
    )
    ax.xaxis.set_ticks(list(plot_data.index))

    return fig


def update_policy(
    policy_obj: tc.Policy,
    reform: Union[TaxcalcReform, ParamToolsAdjustment],
    **kwargs
):
    """
    Convenience method that updates the Policy object with the reform
    dict using the appropriate method, given the reform format.
    """
    if is_paramtools_format(reform):
        policy_obj.adjust(reform, **kwargs)
    else:
        policy_obj.implement_reform(reform, **kwargs)


def is_paramtools_format(reform: Union[TaxcalcReform, ParamToolsAdjustment]):
    """
    Check first item in reform to determine if it is using the ParamTools
    adjustment or the Tax-Calculator reform format.

    If first item is a dict, then it is likely be a Tax-Calculator reform:
    {
        param: {2020: 1000}
    }

    Otherwise, it is likely to be a ParamTools format.

    Returns:
        format (bool): True if reform is likely to be in PT format.
    """
    for param, data in reform.items():
        if isinstance(data, dict):
            return False  # taxcalc reform
        else:
            # Not doing a specific check to see if the value is a list
            # since it could be a list or just a scalar value.
            return True


def volcano_plot(tb, year, y_var="expanded_income", x_var="combined",
                 min_y=0, max_y=9e99, log_scale=True,
                 increase_color="#F15FE4", decrease_color="#41D6C2",
                 dotsize=.75, figsize=(6, 4), dpi=100,
                 xlabel="Change in Tax Liability", ylabel="Expanded Income"):
    """
    Create a volacnoe plot to show change in tax tax liability

    Parameters
    ----------
    tb: TaxBrain instance
    year: year for the plot
    min_y: minimum amount for the y variable to be included in the plot
    max_Y: maximum amount for the y variable to be included in the plot
    y_var: variable on the y axis
    x_var: variable on the x axis
    log_scale: boolean value to indicate if the y-axis should use a log scale.
               If this is true, min_inc must be >= 0
    increase_color: color to use for dots when x increases
    decrease_color: color to use for dots when x decrease
    dotsize: size of the dots in the scatter plot
    figsize: tuple containing the figure size of the plot: (width, height)
    dpi: dots per inch in the figure. A higher value increases image quality
    xlabel: label on the x axis
    ylabel: label on the y axis
    """
    def log_axis(x, pos):
        """
        Converts y-axis log values
        """
        return f"${np.exp(x):,.0f}"

    def axis_formatter(x, pos):
        if x >= 0:
            return f"${x:,.0f}"
        else:
            return f"-${abs(x):,.0f}"

    if log_scale and min_y < 0:
        msg = "`min_y` must be >= 0 when `log_scale` is true"
        raise ValueError(msg)
    _y = tb.base_data[year][y_var]
    _x_change = tb.reform_data[year][x_var] - tb.base_data[year][x_var]
    mask = np.logical_and(_y >= min_y, _y <= max_y)
    y = _y[mask]
    x_change = _x_change[mask]
    colors = np.where(x_change >= 0, increase_color, decrease_color)
    xformatter = ticker.FuncFormatter(axis_formatter)
    yformatter = ticker.FuncFormatter(axis_formatter)
    if log_scale:
        yformatter = ticker.FuncFormatter(log_axis)
        y = np.log(y)
    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(x_change, y, c=colors, s=dotsize)
    ax.axvline(0, color='black', alpha=0.5)
    ax.grid(True, linestyle="--")
    ax.xaxis.set_major_formatter(xformatter)
    ax.xaxis.set_tick_params(rotation=25)
    ax.yaxis.set_major_formatter(yformatter)
    ax.set_xlabel(xlabel, fontweight="bold")
    ax.set_ylabel(ylabel, fontweight="bold")

    return fig
