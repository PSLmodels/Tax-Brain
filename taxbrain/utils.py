"""
Helper functions for the various taxbrain modules
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.ticker as ticker
from collections import defaultdict
from typing import Union, Tuple

import taxcalc as tc
from .typing import ParamToolsAdjustment, TaxcalcReform, PlotColors


def weighted_sum(df, var, wt="s006"):
    """
    Return the weighted sum of specified variable

    Parameters
    ----------
    df: Pandas DataFrame
        data overwhich to compute weighted sum
    var: str
        variable name from df for which to computer weighted sum
    wt: str
        name of weight variable in df

    Returns
    -------
    float
        weighted sum
    """
    return (df[var] * df[wt]).sum()


def distribution_plot(
    tb,
    year: int,
    figsize: Tuple[Union[int, float], Union[int, float]] = (6, 4),
    title: str = "default",
    include_text: bool = False,
):
    """
    Create a horizontal bar chart to display the distributional change in
    after tax income

    Parameters
    ----------
    tb: TaxBrain object
        TaxBrain object for analysis
    year: int
        year to report distribution for
    figsize: tuple
        representing the size of the figure (width, height) in inches
    title: str
        title for plot
    include_text: bool
        whether to include text for labels

    Returns
    -------
    fig: Matplotlib.pyplot figure object
        distribution plot
    """

    def find_percs(data, group):
        """
        Find the percentage of people in the data set that saw
        their income change by the given percentages
        """
        pop = data["s006"].sum()
        large_pos_chng = data["s006"][data["pct_change"] > 5].sum() / pop
        small_pos_chng = (
            data["s006"][
                (data["pct_change"] <= 5) & (data["pct_change"] > 1)
            ].sum()
            / pop
        )
        small_chng = (
            data["s006"][
                (data["pct_change"] <= 1) & (data["pct_change"] >= -1)
            ].sum()
            / pop
        )
        small_neg_change = (
            data["s006"][
                (data["pct_change"] < -1) & (data["pct_change"] > -5)
            ].sum()
            / pop
        )
        large_neg_change = data["s006"][data["pct_change"] < -5].sum() / pop

        return (
            large_pos_chng,
            small_pos_chng,
            small_chng,
            small_neg_change,
            large_neg_change,
        )

    # extract needed data from the TaxBrain object
    ati_data = pd.DataFrame(
        {
            "base": tb.base_data[year]["aftertax_income"],
            "reform": tb.reform_data[year]["aftertax_income"],
            "s006": tb.base_data[year]["s006"],
        }
    )
    ati_data["diff"] = ati_data["reform"] - ati_data["base"]
    ati_data["pct_change"] = (ati_data["diff"] / ati_data["base"]) * 100
    ati_data = ati_data.fillna(0.0)  # fill in NaNs for graphing
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
        (-9e99, 10000, "Less than $10K"),
    ]

    plot_data = defaultdict(list)
    # traverse list in reverse to get the axis of the plot in correct order
    for low, high, grp in groups:
        # find income changes by group
        sub_data = ati_data[
            (ati_data["base"] <= high) & (ati_data["base"] > low)
        ]
        results = find_percs(sub_data, grp)
        plot_data[grp] = results

    legend_labels = [
        "Increase of > 5%",
        "Increase 1-5%",
        "Change < 1%",
        "Decrease of 1-5%",
        "Decrease > 5%",
    ]
    labels = list(plot_data.keys())
    data = np.array(list(plot_data.values()))
    data_cumsum = data.cumsum(axis=1)
    category_colors = plt.get_cmap("GnBu")(
        np.linspace(0.15, 0.85, data.shape[1])
    )

    fig, ax = plt.subplots(figsize=figsize)
    ax.invert_yaxis()
    ax.set_xlim(0, np.sum(data, axis=1).max())

    for i, (colname, color) in enumerate(zip(legend_labels, category_colors)):
        widths = data[:, i]
        starts = data_cumsum[:, i] - widths
        ax.barh(
            labels, widths, left=starts, height=0.9, label=colname, color=color
        )
        if include_text:
            # add text label
            xcenters = starts + widths / 2
            r, g, b, _ = color
            text_color = "white" if r * g * b < 0.5 else "darkgrey"
            for y, (x, c) in enumerate(zip(xcenters, widths)):
                ax.text(
                    x,
                    y,
                    f"{c * 100:.1f}%",
                    ha="center",
                    va="center",
                    color=text_color,
                )
    ax.legend(bbox_to_anchor=(1, 1), loc="upper left", fontsize="small")
    ax.set_xlabel("Portion of Bin", fontweight="bold")
    ax.set_ylabel("Expanded Income Bin", fontweight="bold")
    ax.get_xaxis().set_major_formatter(
        mpl.ticker.FuncFormatter(lambda x, p: format(f"{int(x * 100)}%"))
    )
    if title == "default":
        title = f"Percentage Change In After Tax Income - {year}"
    ax.set_title(title)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", which="both", length=0, pad=15)

    return fig


def differences_plot(
    tb,
    tax_type: str,
    figsize: Tuple[Union[int, float], Union[int, float]] = (6, 4),
    title: str = "default",
):
    """
    Create a bar chart that shows the change in total liability for a given
    tax

    Parameters
    ----------
    tb: TaxBrain object
        TaxBrain object for analysis
    tax_type: str
        tax for which to show the change in liability
        options: 'income', 'payroll', 'combined'
    figsize: tuple
        representing the size of the figure (width, height) in inches
    title: str
        title for plot

    Returns
    -------
    fig: Matplotlib.pyplot figure object
        differences plot
    """

    def axis_formatter(x, p):
        if x >= 0:
            return f"${x * 1e-9:,.2f}b"
        else:
            return f"-${x * 1e-9:,.2f}b"

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
    ax.grid(True, axis="y", alpha=0.55)
    ax.set_axisbelow(True)
    ax.bar(
        plot_data.index,
        plot_data["combined"],
        alpha=0.55,
        color=plot_data["color"],
    )
    if title == "default":
        title = f"Change in Aggregate {tax_type.title()} Tax Liability"
    ax.set_title(title)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.get_yaxis().set_major_formatter(
        mpl.ticker.FuncFormatter(axis_formatter)
    )
    ax.xaxis.set_ticks(list(plot_data.index))
    ax.xaxis.set_major_formatter(mpl.ticker.ScalarFormatter(useOffset=False))

    return fig


def update_policy(
    policy_obj: tc.Policy,
    reform: Union[TaxcalcReform, ParamToolsAdjustment],
    **kwargs,
):
    """
    Convenience method that updates the Policy object with the reform
    dict using the appropriate method, given the reform format.

    Parameters
    ----------
    policy_obj: Tax-Calculator Policy class object
        Policy object for tax parameterization used for analysis
    reform: str or dict
        parameters for tax policy

    Returns
    -------
    None
        modifies the Policy object
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

    Parameters
    ----------
    reform: str or dict
        parameters for tax policy

    Returns
    -------
    bool
        True if reform is likely to be in ParamTools format
    """
    for param, data in reform.items():
        if isinstance(data, dict):
            return False  # taxcalc reform
        else:
            # Not doing a specific check to see if the value is a list
            # since it could be a list or just a scalar value.
            return True


def lorenz_data(tb, year: int, var: str = "aftertax_income"):
    """
    Pull data used for the lorenz curve plot

    Parameters
    ----------
    tb: TaxBrain class object
        TaxBrain object for analysis
    year: int
        year of data to use
    var: str
        name of the variable to use

    Returns
    -------
    final_data: Pandas DataFrame
        DataFrame with Lorenz curve for baseline and reform
    """
    data = pd.DataFrame(
        {
            "base": tb.base_data[year][var],
            "reform": tb.reform_data[year][var],
            "wt": tb.base_data[year]["s006"],
        }
    )
    data["wt_base"] = data["base"] * data["wt"]
    data["wt_reform"] = data["reform"] * data["wt"]
    data.sort_values("base", inplace=True)
    data["cwt"] = data["wt"].cumsum()
    data["percentile"] = data["cwt"] / data["wt"].sum()
    # each bin has 1% of the population
    _bins = np.arange(0, 1.01, step=0.01)
    data["bin"] = pd.cut(data["percentile"], bins=_bins)
    gdf = data.groupby("bin", observed=False)
    base = gdf["wt_base"].sum()
    base = np.where(base < 0, 0, base)
    reform = gdf["wt_reform"].sum()
    reform = np.where(reform < 0, 0, reform)
    final_data = pd.DataFrame(
        {
            "Base": base.cumsum() / data["wt_base"].sum(),
            "Reform": reform.cumsum() / data["wt_reform"].sum(),
            "Population": gdf["wt"].sum().cumsum() / data["wt"].sum(),
        }
    )

    return final_data


def lorenz_curve(
    tb,
    year: int,
    var: str = "aftertax_income",
    figsize: Tuple[Union[int, float], Union[int, float]] = (6, 4),
    xlabel: str = "Cummulative Percentage of Tax Units",
    ylabel: str = "Cummulative Percentage of Income",
    base_color: PlotColors = "blue",
    base_linestyle: str = "-",
    reform_color: PlotColors = "red",
    reform_linestyle: str = "--",
    dpi: Union[int, float] = 100,
):
    """
    Generate a Lorenz Curve

    Parameters
    ----------
    tb: TaxBrain class object
        TaxBrain object for analysis
    year: int
        year of data you want to use for the lorenz curve
    var: str
        name of the variable to use
    figsize: tuple
        representing the size of the figure (width, height) in inches
    xlabel: str
        x axis label
    ylabel: str
        y axis label
    base_color: str
        color used for the base line
    base_linestyle: str
        linestyle for the base line
    reform_color: str
        color used for the reform line
    reform_linestyle: str
        linestyle for the reform line
    dpi: int
        dots per inch in the figure image

    Returns
    -------
    None
    """
    plot_data = lorenz_data(tb, year, var)
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot([0, 1], [0, 1], c="black", alpha=0.5)  # 45 degree line
    ax.plot(
        plot_data["Population"],
        plot_data["Base"],
        c=base_color,
        linestyle=base_linestyle,
        label="Base",
    )
    ax.plot(
        plot_data["Population"],
        plot_data["Reform"],
        c=reform_color,
        linestyle=reform_linestyle,
        label="Reform",
    )
    ax.legend(loc="upper left")
    ax.set_xlabel(xlabel, fontweight="bold")
    ax.set_ylabel(ylabel, fontweight="bold")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    return fig


def volcano_plot(
    tb,
    year: int,
    y_var: str = "expanded_income",
    x_var: str = "combined",
    min_y: Union[int, float] = 0.01,
    max_y: Union[int, float] = 9e99,
    log_scale: bool = True,
    increase_color: PlotColors = "#F15FE4",
    decrease_color: PlotColors = "#41D6C2",
    dotsize: Union[int, float] = 0.75,
    alpha: float = 0.5,
    figsize: Tuple[Union[int, float], Union[int, float]] = (6, 4),
    dpi: Union[int, float] = 100,
    xlabel: str = "Change in Tax Liability",
    ylabel: str = "Expanded Income",
):
    """
    Create a volcano plot to show change in tax tax liability

    Parameters
    ----------
    tb: TaxBrain class object
        TaxBrain object for analysis
    year: int
        year for the plot
    min_y: float
        minimum amount for the y variable to be included in the plot
    max_y: float
        maximum amount for the y variable to be included in the plot
    y_var: str
        variable on the y axis
    x_var: str
        variable on the x axis
    log_scale: bool
        whether the y-axis should use a log scale. If this is true,
        min_inc must be >= 0
    increase_color: str
        color to use for dots when x increases
    decrease_color: str
        color to use for dots when x decrease
    dotsize: int
        size of the dots in the scatter plot
    alpha: float
        attribute for transparency of the dots
    figsize: tuple
        the figure size of the plot (width, height) in inches
    dpi: int
        dots per inch in the figure
    xlabel: str
        label on the x axis
    ylabel: str
        label on the y axis

    Returns
    -------
    fig: Matplotlib.pyplot figure object
        volcano plot figure
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
    colors = [increase_color if x >= 0 else decrease_color for x in x_change]
    xformatter = ticker.FuncFormatter(axis_formatter)
    yformatter = ticker.FuncFormatter(axis_formatter)
    if log_scale:
        yformatter = ticker.FuncFormatter(log_axis)
        y = np.log(y)
    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(x_change, y, c=colors, s=dotsize, alpha=alpha)
    ax.axvline(0, color="black", alpha=0.5)
    ax.grid(True, linestyle="--")
    ax.xaxis.set_major_formatter(xformatter)
    ax.xaxis.set_tick_params(rotation=25)
    ax.yaxis.set_major_formatter(yformatter)
    ax.set_xlabel(xlabel, fontweight="bold")
    ax.set_ylabel(ylabel, fontweight="bold")

    return fig


def revenue_plot(
    tb,
    tax_vars: list = ["iitax", "payrolltax", "combined"],
    figsize: Tuple[Union[int, float], Union[int, float]] = (6, 4),
):
    """Plot the changes in tax revenue from a given reform

    Parameters
    ----------
    tb : TaxBrain class object
        TaxBrain object for analysis
    tax_vars: list
        List of tax varaibles to include on the graph
    """

    def axis_formatter(x, p):
        if x >= 0:
            return f"${x * 1e-9:,.2f}"
        else:
            return f"-${x * 1e-9:,.2f}"

    assert tax_vars, "`tax_vars` must contain at least one tax variable"
    for var in tax_vars:
        if var not in ["iitax", "payrolltax", "combined"]:
            msg = (
                f"`{var}` is invalid. Valid tax variables are "
                "`iitax`, `payrolltax`, `combined`"
            )
            raise ValueError(msg)
    label_map = {
        "iitax": "Income",
        "payrolltax": "Payroll",
        "combined": "Combined",
    }
    color_map = {
        "Income: Base": "#12719e",
        "Income: Reform": "#73bfe2",
        "Payroll: Base": "#408941",
        "Payroll: Reform": "#98cf90",
        "Combined: Base": "#a4201d",
        "Combined: Reform": "#e9807d",
    }
    base_data = tb.multi_var_table(tax_vars, "base", include_total=False)
    reform_data = tb.multi_var_table(tax_vars, "reform", include_total=False)
    fig, ax = plt.subplots(figsize=figsize)
    years = base_data.columns
    for tax in tax_vars:
        base_label = f"{label_map[tax]}: Base"
        reform_label = f"{label_map[tax]}: Reform"
        ax.plot(
            years,
            base_data.loc[tax],
            label=base_label,
            color=color_map[base_label],
        )
        ax.plot(
            years,
            reform_data.loc[tax],
            label=reform_label,
            color=color_map[reform_label],
        )

    ax.legend(loc="upper right", bbox_to_anchor=(1.40, 1), title="Tax Type")
    ax.set_ylabel("Tax Liability (Billions)")
    ax.set_title("Tax Liability by Year")
    # remove plot borders
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    # convert y axis to billions
    ax.get_yaxis().set_major_formatter(
        mpl.ticker.FuncFormatter(axis_formatter)
    )
    return fig
