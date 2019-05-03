"""
Functions for creating the TaxBrain COMP outputs
"""
from bokeh.models.widgets import Tabs, Panel, Div
from bokeh.embed import components
from bokeh.layouts import layout, column


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
                        title="Current Law", sizing_mode="fixed")
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

    lo = layout(
        children=[
            [column([agg_tabs, yr_tabs])]
        ]
    )
    js, div = components(lo)

    # return a dictionary of outputs ready for COMP
    outputs = {
        "media_type": "bokeh",
        "title": "Results",
        "data": {
            "javascript": js,
            "html": div
        }
    }

    # return js, div, cdn_js, cdn_css, widget_js, widget_css
    return outputs
