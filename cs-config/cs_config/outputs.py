"""
Functions for creating the TaxBrain COMP outputs
"""
from bokeh.models import (ColumnDataSource, Toggle, CustomJS,
                          NumeralTickFormatter, HoverTool)
from bokeh.models.widgets import Tabs, Panel, Div
from bokeh.embed import components
from bokeh.layouts import layout
from bokeh.plotting import figure


def aggregate_plot(tb):
    """
    Function for creating a bokeh plot that shows aggregate tax liabilities for
    each year the TaxBrain instance was run
    Parameters
    ----------
    tb: An instance of the TaxBrain object
    Returns
    -------
    Bokeh figure
    """
    # Pull aggregate data by year and transpose it for plotting
    varlist = ["iitax", "payrolltax", "combined"]
    base_data = tb.multi_var_table(varlist, "base").transpose()
    base_data["calc"] = "Base"
    reform_data = tb.multi_var_table(varlist, "reform").transpose()
    reform_data["calc"] = "Reform"
    base_cds = ColumnDataSource(base_data)
    reform_cds = ColumnDataSource(reform_data)
    num_ticks = len(base_data)
    del base_data, reform_data

    fig = figure(title="Aggregate Tax Liability by Year",
                 width=700, height=500, tools="save")
    ii_base = fig.line(x="index", y="iitax", line_width=4,
                       line_color="#12719e", legend="Income Tax - Base",
                       source=base_cds)
    ii_reform = fig.line(x="index", y="iitax", line_width=4,
                         line_color="#73bfe2", legend="Income Tax - Reform",
                         source=reform_cds)
    proll_base = fig.line(x="index", y="payrolltax", line_width=4,
                          line_color="#408941", legend="Payroll Tax - Base",
                          source=base_cds)
    proll_reform = fig.line(x="index", y="payrolltax", line_width=4,
                            line_color="#98cf90", legend="Payroll Tax - Reform",
                            source=reform_cds)
    comb_base = fig.line(x="index", y="combined", line_width=4,
                         line_color="#a4201d", legend="Combined - Base",
                         source=base_cds)
    comb_reform = fig.line(x="index", y="combined", line_width=4,
                           line_color="#e9807d", legend="Combined - Reform",
                           source=reform_cds)

    # format figure
    fig.legend.location = "top_left"
    fig.yaxis.formatter = NumeralTickFormatter(format="$0.00a")
    fig.yaxis.axis_label = "Aggregate Tax Liability"
    fig.xaxis.minor_tick_line_color = None
    fig.xaxis[0].ticker.desired_num_ticks = num_ticks

    # Add hover tool
    tool_str = """
        <p><b>@calc - {}</b></p>
        <p>${}</p>
    """
    ii_hover = HoverTool(
        tooltips=tool_str.format("Individual Income Tax", "@iitax{0,0}"),
        renderers=[ii_base, ii_reform]
    )
    proll_hover = HoverTool(
        tooltips=tool_str.format("Payroll Tax", "@payrolltax{0,0}"),
        renderers=[proll_base, proll_reform]
    )
    combined_hover = HoverTool(
        tooltips=tool_str.format("Combined Tax", "@combined{0,0}"),
        renderers=[comb_base, comb_reform]
    )
    fig.add_tools(ii_hover, proll_hover, combined_hover)

    # toggle which lines are shown
    plot_js = """
    object1.visible = toggle.active
    object2.visible = toggle.active
    object3.visible = toggle.active
    """
    base_callback = CustomJS.from_coffeescript(code=plot_js, args={})
    base_toggle = Toggle(label="Base", button_type="primary",
                         callback=base_callback, active=True)
    base_callback.args = {"toggle": base_toggle, "object1": ii_base,
                          "object2": proll_base, "object3": comb_base}

    reform_callback = CustomJS.from_coffeescript(code=plot_js, args={})
    reform_toggle = Toggle(label="Reform", button_type="primary",
                           callback=reform_callback, active=True)
    reform_callback.args = {"toggle": reform_toggle, "object1": ii_reform,
                            "object2": proll_reform, "object3": comb_reform}
    fig_layout = layout([fig], [base_toggle, reform_toggle])

    # Components needed to embed the figure
    js, div = components(fig_layout)
    outputs = {
        "media_type": "bokeh",
        "title": "",
        "data": {
            "javascript": js,
            "html": div
        }
    }

    return outputs


def create_layout(data, start_year, end_year):
    """
    Function for creating a bokeh layout with all of the data tables
    """

    agg_data = data["aggr_outputs"]
    # create aggregate table
    clt_title = f"<h3>{agg_data['current']['title']}</h3>"
    current_law_table = Div(text=clt_title + agg_data["current"]["renderable"],
                            width=1000)
    rt_title = f"<h3>{agg_data['reform']['title']}</h3>"
    reform_table = Div(text=rt_title + agg_data["reform"]["renderable"],
                       width=1000)
    ct_title = f"<h3>{agg_data['change']['title']}</h3>"
    change_table = Div(text=ct_title + agg_data["change"]["renderable"],
                       width=1000)

    current_tab = Panel(child=current_law_table,
                        title="Current Law")
    reform_tab = Panel(child=reform_table,
                       title="Reform")
    change_tab = Panel(child=change_table,
                       title="Change")
    agg_tabs = Tabs(tabs=[current_tab, reform_tab, change_tab])

    key_map = {
        "current": "Current",
        "reform": "Reform",
        "ind_income": "Income Tax",
        "payroll": "Payroll Tax",
        "combined": "Combined Tax",
        "dist": "Distribution Table",
        "diff": "Differences Table"
    }

    tbl_data = data["tbl_outputs"]
    yr_panels = []
    # loop through each year (start - end year)
    for yr in range(start_year, end_year + 1):
        # loop through each table type: dist, idff
        tbl_panels = []
        for tbl_type, content in tbl_data.items():
            # loop through sub tables: current, reform for dist
            # ind_income, payroll, combined for diff
            content_panels = []
            for key, value in content.items():
                # loop through each grouping: bins, deciles
                grp_panels = []
                for grp, grp_data in value.items():
                    _data = grp_data[yr]
                    # create a data table for this tab
                    title = f"<h3>{_data['title']}</h3>"
                    note = ("<p><i>All monetary values are in billions. "
                            "All non-monetary values are in millions.</i></p>")
                    tbl = Div(text=title + note + _data["renderable"],
                              width=1000)
                    grp_panel = Panel(child=tbl, title=grp.title())
                    grp_panels.append(grp_panel)
                grp_tab = Tabs(tabs=grp_panels)
                # panel for the sub tables
                content_panel = Panel(child=grp_tab, title=key_map[key])
                content_panels.append(content_panel)
            content_tab = Tabs(tabs=content_panels)
            # panel for the table types
            tbl_panel = Panel(child=content_tab,
                              title=key_map[tbl_type])
            tbl_panels.append(tbl_panel)
        type_tab = Tabs(tabs=tbl_panels)
        # panel for the year
        yr_panel = Panel(child=type_tab, title=str(yr))
        yr_panels.append(yr_panel)

    yr_tabs = Tabs(tabs=yr_panels)

    agg_layout = layout(
        children=[agg_tabs]
    )
    table_layout = layout(
        children=[yr_tabs]
    )
    agg_js, agg_div = components(agg_layout)
    table_js, table_div = components(table_layout)

    # return a dictionary of outputs ready for COMP
    agg_outputs = {
        "media_type": "bokeh",
        "title": "Aggregate Results",
        "data": {
            "javascript": agg_js,
            "html": agg_div
        }
    }
    table_outputs = {
        "media_type": "bokeh",
        "title": "Tables",
        "data": {
            "javascript": table_js,
            "html": table_div
        }
    }

    # return js, div, cdn_js, cdn_css, widget_js, widget_css
    return agg_outputs, table_outputs
