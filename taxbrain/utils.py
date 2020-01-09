"""
Helper functions for the various taxbrain modules
"""
import pandas as pd
import numpy as np
from bokeh.plotting import figure
from bokeh.models import (ColumnDataSource, NumeralTickFormatter,
                          CategoricalAxis, CategoricalTicker)
from bokeh.palettes import GnBu5
from collections import defaultdict


def weighted_sum(df, var, wt="s006"):
    """
    Return the weighted sum of specified variable
    """
    return (df[var] * df[wt]).sum()


def distribution_plot(tb, year, width=500, height=400, export_svg=False):
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
    for low, high, grp in groups[:: -1]:
        # find income changes by group
        sub_data = ati_data[(ati_data["base"] <= high) &
                            (ati_data["base"] > low)]
        results = find_percs(sub_data, grp)
        plot_data["group"].append(grp)
        plot_data["large_pos"].append(results[0])
        plot_data["small_pos"].append(results[1])
        plot_data["small"].append(results[2])
        plot_data["small_neg"].append(results[3])
        plot_data["large_neg"].append(results[4])

    # groups used for plotting
    change_groups = [
        "large_pos", "small_pos", "small", "small_neg", "large_neg"
    ]
    legend_labels = [
        "Increase of > 5%", "Increase 1-5%", "Change < 1%",
        "Decrease of 1-5%", "Decrease > 5%"
    ]
    plot = figure(
        y_range=plot_data["group"], x_range=(0, 1), toolbar_location=None,
        width=width, height=height,
        title=f"Percentage Change in After Tax Income - {year}"
    )
    plot.hbar_stack(
        change_groups, y="group", height=0.8, color=GnBu5,
        source=ColumnDataSource(plot_data),
        legend=legend_labels
    )
    # general formatting
    plot.yaxis.axis_label = "Expanded Income Bin"
    plot.xaxis.axis_label = "Portion of Population"
    plot.xaxis.formatter = NumeralTickFormatter(format="0%")
    plot.xaxis.minor_tick_line_color = None
    # move legend out of main plot area
    legend = plot.legend[0]
    plot.add_layout(legend, "right")
    if export_svg:
        plot.output_backend = "svg"

    return plot


def differences_plot(tb, tax_type, width=500, height=400, export_svg=False):
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

    plot = figure(
        title=f"Change in Aggregate {tax_type.title()} Tax Liability",
        width=width, height=height, toolbar_location=None
    )
    if export_svg:
        plot.output_backend = "svg"
    plot.vbar(
        x="index", bottom=0, top=tax_var, width=0.7,
        source=ColumnDataSource(plot_data),
        fill_color="color", line_color="color",
        fill_alpha=0.55
    )
    # general formatting
    plot.yaxis.formatter = NumeralTickFormatter(format="($0.00 a)")
    plot.xaxis.formatter = NumeralTickFormatter(format="0")
    plot.xaxis.minor_tick_line_color = None
    plot.xgrid.grid_line_color = None

    return plot
