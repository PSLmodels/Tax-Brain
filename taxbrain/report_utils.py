"""
Helper Functions for creating the automated reports
"""

import json
import pypandoc
import numpy as np
import pandas as pd
import taxcalc as tc
from jinja2 import Template
from pathlib import Path
from datetime import datetime
from tabulate import tabulate
from collections import defaultdict, deque
from .utils import is_paramtools_format
from typing import Union


CUR_PATH = Path(__file__).resolve().parent

notable_vars = {
    "c00100": "AGI",
    "count_standard": "Number of standard deduction filers",
    "standard": "Standard deduction amount",
    "count_c04470": "Number of itemizers",
    "c04470": "Total itemized deductions",
    "c04600": "Personal exemptions",
    "c04800": "Taxable income",
    "c62100": "Total AMT income",
    "count_c09600": "Number of AMT filers",
    "c09600": "Total AMT",
    "c05800": "Total tax liability before credits",
    "c07100": "Total non-refundable credits",
    "refund": "Total refundable credits",
    "ubi": "Universal Basic Income",
    "benefit_cost_total": "Spending on benefit programs",
    "benefit_value_total": "Consumption value of benefits",
    "expanded_income": "Expanded income",
    "aftertax_income": "After-tax income",
}

DIFF_TABLE_ROW_NAMES = [
    "<$0K",
    "=$0K",
    "$0-10K",
    "$10-20K",
    "$20-30K",
    "$30-40K",
    "$40-50K",
    "$50-75K",
    "$75-100K",
    "$100-200K",
    "$200-500K",
    "$500K-1M",
    ">$1M",
    "ALL",
]


def md_to_pdf(md_text, outputfile_path):
    """
    Convert Markdown version of report to a PDF. Returns bytes that can be
    saved as a PDF

    Parameters
    ----------
    md_text: str
        report template written in markdown
    outputfile_path: str
        path to where the final file sohould be written

    Returns
    -------
    None
        Markdown text is saved as a PDF and the HTML used to create
        the report
    """
    # convert markdown text to pdf with pandoc
    pypandoc.convert_text(
        md_text,
        "pdf",
        format="md",
        outputfile=outputfile_path,
        extra_args=["-V", "geometry:margin=1.5cm", "--pdf-engine", "pdflatex"],
    )


def convert_table(df, tablefmt: str = "pipe") -> str:
    """
    Convert pandas DataFrame to Markdown style table

    Parameters
    ----------
    df: Pandas DataFrame
        DataFrame to convert

    Returns
    -------
    str
        String that is a formatted markdown table
    """
    if isinstance(df, pd.DataFrame):
        return tabulate(df, headers="keys", tablefmt=tablefmt)
    else:
        return tabulate(df, headers="firstrow", tablefmt=tablefmt)


def policy_table(params):
    """
    Create a table showing the policy parameters in a reform and their
    default value

    Parameters
    ----------
    params: dict
        policy parameters being implemented

    Returns
    -------
    md_tables: str
        String containing a markdown style table that summarized the
        given parameters
    """
    # map out additional name information for vi indexed variables
    vi_map = {
        "MARS": [
            "Single",
            "Married Filing Jointly",
            "Married Filing Separately",
            "Head of Household",
            "Widow",
        ],
        "idedtype": [
            "Medical",
            "State & Local Taxes",
            "Real EState Taxes",
            "Casualty",
            "Miscellaneous",
            "Interest Paid",
            "Charitable Giving",
        ],
        "EIC": ["0 Kids", "1 Kid", "2 Kids", "3+ Kids"],
    }
    reform_years = set()
    reform_by_year = defaultdict(lambda: deque())
    if is_paramtools_format(params):
        params = convert_params(params)
    pol = tc.Policy()  # policy object used for getting original value
    # loop through all of the policy parameters in a given reform
    for param, meta in params.items():
        # find all the years the parameter is updated
        years = set(meta.keys())
        reform_years = reform_years.union(years)
        for yr in years:
            # find default information
            pol.set_year(yr)
            if param.endswith("-indexed"):
                _param = param.split("-")[0]
                pol_meta = pol.metadata()[_param]
                default_indexed = pol_meta["indexed"]
                new_indexed = meta[yr]
                name = pol_meta["title"]
                reform_by_year[yr].append(
                    [
                        name,
                        f"CPI Indexed: {default_indexed}",
                        f"CPI Indexed: {new_indexed}",
                    ]
                )
                continue
            pol_meta = pol.metadata()[param]
            name = pol_meta["title"]
            default_val = getattr(pol, param)
            new_val = meta[yr]
            # skip any duplicated policy parameters
            if np.all(default_val == new_val):
                continue
            # create individual lines for indexed parameters
            # think parameters that vary by marital status, number of kids, etc
            if len(default_val.shape) != 1:
                # first find the indexed parameter we're working with
                for vi in vi_map.keys():
                    if vi in pol_meta["value"][0].keys():
                        vi_name = vi
                        break
                vi_list = vi_map[vi_name]
                for i, val in enumerate(default_val[0]):
                    # print(name, val, param, default_val)
                    _name = f"{name} - {vi_list[i]}"
                    _default_val = f"{val:,}"
                    _new_val = f"{new_val[i]:,}"
                    if _default_val == _new_val:
                        continue
                    reform_by_year[yr].append([_name, _default_val, _new_val])
            else:
                reform_by_year[yr].append(
                    [name, f"{default_val[0]:,}", f"{new_val:,}"]
                )

    # convert all tables from CSV format to Markdown
    md_tables = {}
    for yr in reform_years:
        content = reform_by_year[yr]
        content.appendleft(["Policy", "Original Value", "New Value"])
        md_tables[yr] = convert_table(content)

    return md_tables


def write_text(template_path, **kwargs):
    """
    Fill in text with specified template

    Parameters
    ----------
    template_path: str
        path to read template from

    Returns
    -------
    rendered: str
        rendered template
    """
    template_str = Path(template_path).open("r").read()
    template = Template(template_str)
    rendered = template.render(**kwargs)

    return rendered


def date():
    """
    Return formatted date

    Parameters
    ----------
    None

    Returns
    --------
    None
    """
    today = datetime.today()
    month = today.strftime("%B")
    day = today.day
    year = today.year
    date = f"{month} {day}, {year}"
    return date


def form_intro(pol_areas, description=None):
    """
    Form the introduction line

    Parameters
    ----------
    pol_areas: list
        list of all the policy areas included in the reform used to
        create a description of the reform
    description: str
        user provided description of the reform

    Returns
    -------
    str
        introduction text for report
    """
    # these are all of the possible strings used in the introduction sentance
    intro_text = {
        1: "modifing the {} section of the tax code",
        2: "modifing the {} and {} sections of the tax code",
        3: "modifing the {}, {}, and {} sections of the tax code",
        4: (
            "modifing a number of areas of the tax code, "
            "including the {}, {}, and {} sections"
        ),
    }
    if not description:
        num_areas = min(len(pol_areas), 4)
        intro_line = intro_text[num_areas]
        if num_areas == 1:
            return intro_line.format(pol_areas[0])
        elif num_areas == 2:
            return intro_line.format(pol_areas[0], pol_areas[1])
        else:
            return intro_line.format(pol_areas[0], pol_areas[1], pol_areas[2])
    else:
        return description


def form_baseline_intro(current_law):
    """
    Form final sentence of introduction paragraph

    Parameters
    -----------
    current_law: bool
        whether report is for the current law baseline

    Returns
    -------
    str
        text or intro of baseline summary
    """
    if not current_law:
        return f"{date()}"
    else:
        return (
            f"{date()}, along with some modifications. A summary of these "
            'modifications can be found in the "Summary of Baseline Policy" '
            "section"
        )


def largest_tax_change(diff):
    """
    Function to find the largest change in tax liability

    Parameters
    ----------
    diff: Pandas DataFrame
        Differences table created by taxbrain

    Returns
    -------
    largest_change_group: str
        string relating group with the largest change
    largest_change_str: str
        string relating size of largest change
    """
    sub_diff = diff.drop(index="ALL")  # remove total row
    # find the absolute largest change in total liability
    absolute_change = abs(sub_diff["tot_change"])
    largest = sub_diff[max(absolute_change) == absolute_change]
    index_largest = largest.index.values[0]
    largest_change = largest["mean"].values[0]  # index in case there"s a tie
    # split index to form sentance
    split_index = index_largest.split("-")
    if len(split_index) == 1:
        index_name = split_index[0][1:]
        direction = split_index[0][0]
        if direction == ">":
            direction_str = "greater than"
        elif direction == "<":
            direction_str = "less than"
        else:
            direction_str = "equal to"
        largest_change_group = f"{direction_str} {index_name}"
    else:
        largest_change_group = f"between {split_index[0]} and {split_index[1]}"

    formatted_change = dollar_str_formatting(largest_change)
    if largest_change < 0:
        largest_change_str = f"decrease by ${formatted_change}"
    elif largest_change > 0:
        largest_change_str = f"increase by ${formatted_change}"
    else:
        largest_change_str = "remain the same"

    return largest_change_group, largest_change_str


def notable_changes(tb, threshold: float) -> str:
    """
    Find any notable changes in certain variables. "Notable" is defined
    as a percentage change above the given threshold.

    Parameters
    ----------
    tb: TaxBrain object
        instance of TaxBrain object for analysis
    threshold: float
        Percentage change in an aggregate variable for it to be
        considered notable

    Returns
    -------
    section: str
        text for section on notable changes
    """
    notable_dict = defaultdict(list)
    # loop through all of the notable variables and see if there is a year
    # where they change more than the given threshold
    for var, desc in notable_vars.items():
        if var.startswith("count_"):
            # count number of filers with a non-zero value for a given variable
            totals = []
            years = []
            for year in range(tb.start_year, tb.end_year + 1):
                _var = var.split("_")[1]
                base = tb.base_data[year]
                reform = tb.reform_data[year]
                base_total = np.where(base[_var] != 0, base["s006"], 0).sum()
                reform_total = np.where(
                    reform[_var] != 0, reform["s006"], 0
                ).sum()
                diff = reform_total - base_total
                totals.append(
                    {
                        "Base": base_total,
                        "Reform": reform_total,
                        "Difference": diff,
                    }
                )
                years.append(year)
            totals = pd.DataFrame(totals)
            totals.index = years
        else:
            totals = tb.weighted_totals(var).transpose()
        totals["pct_change"] = totals["Difference"] / totals["Base"]
        totals = totals.fillna(0.0)
        max_pct_change = max(totals["pct_change"])
        max_yr = totals[totals["pct_change"] == max_pct_change].index.values[0]
        if abs(max_pct_change) >= threshold:
            if max_pct_change < 0:
                direction = "decreases"
            else:
                direction = "increases"
            pct_chng = max_pct_change * 100
            notable_str = f"{desc} {direction} by {pct_chng:.2f}%"
            notable_dict[max_yr].append(notable_str)
    # add default message if no notable changes
    min_chng = threshold * 100
    section = [f"No notable variables changed by more than {min_chng:.2f}%"]
    if notable_dict:
        section = []
        for year, item in notable_dict.items():
            section.append(f"_{year}_")
            for change in item:
                section.append(f"* {change}")
    return section


def behavioral_assumptions(tb):
    """
    Return list of behavioral assumptions used

    Parameters
    ----------
    tb: TaxBrain object
        instance of TaxBrain object for analysis

    Returns
    -------
    assumptions: list
        list of behavioral assumptions used
    """
    behavior_map = {
        "sub": "Substitution elasticity of taxable income: {}",
        "inc": "Income elasticity of taxable income: {}",
        "cg": "Semi-elasticity of long-term capital gains: {}",
    }
    assumptions = []
    # if there are some behavioral assumptions, loop through them
    if tb.params["behavior"]:
        for param, val in tb.params["behavior"].items():
            assumptions.append(behavior_map[param].format(val))
    else:
        assumptions.append("No behavioral assumptions")
    return assumptions


def consumption_assumptions(tb):
    """
    Create table of consumption assumptions used in analysis

    Parameters
    ----------
    tb: TaxBrain object
        instance of TaxBrain object for analysis

    Returns
    -------
    md_tables: str
        table of consumption assumptions for report
    """
    if tb.params["consumption"]:
        params = tb.params["consumption"]
        # create table of consumption assumptions
        consump_years = set()
        consump_by_year = defaultdict(lambda: deque())
        # read consumption.json from taxcalc package
        consump_json = (
            Path(Path(tc.__file__).resolve().parent, "consumption.json")
            .open("r")
            .read()
        )
        consump_meta = json.loads(consump_json)
        for param, meta in params.items():
            # find all the years the parameter is updated
            years = set(meta.keys())
            consump_years = consump_years.union(years)
            name = consump_meta[param]["title"]
            default_val = consump_meta[param]["value"][0]
            for yr in years:
                # find default information
                new_val = meta[yr]
                consump_by_year[yr].append([name, default_val, new_val])
        md_tables = {}  # hold markdown version of the tables
        for yr in consump_years:
            content = consump_by_year[yr]
            content.appendleft(["", "Default Value", "User Value"])
            md_tables[yr] = convert_table(content)
        return md_tables
    else:
        msg = "No new consumption assumptions specified."
        return {"": msg}


def growth_assumptions(tb):
    """
    Create a table with all of the growth assumptions used in the analysis

    Parameters
    ----------
    tb: TaxBrain object
        instance of TaxBrain object for analysis

    Returns
    -------
    md_tables: str
        table of growth assumptions for report
    """
    growth_vars_map = {
        "ABOOK": "General Business and Foreign Tax Credit Growth Rate",
        "ACGNS": "Capital Gains Growth Rate",
        "ACPIM": "CPI - Medical",
        "ACPIU": "CPI - Urban Consumer",
        "ADIV": "Dividend Income Growth Rate",
        "AINTS": "Interest Income Growth Rate",
        "AIPD": "Interest Paid Deduction Growth Rate",
        "ASCHCI": "Schedule C Income Growth Rate",
        "ASCHCL": "Schedule C Losses Growth Rate",
        "ASCHEI": "Schedule E Income Growth Rate",
        "ASCHEL": "Schedule E Losses Growth Rate",
        "ASCHFI": "Schedule F Income Growth Rate",
        "ASCHFL": "Schedule F Losses Growth Rate",
        "ASOCSEC": "Social Security Benefit Growth Rate",
        "ATXPY": "Personal Income Growth Rate",
        "AUCOMP": "Unemployment Compensation Growth Rate",
        "AWAGE": "Wage Income Growth Rate",
        "ABENOTHER": "Other Benefits Growth Rate",
        "ABENMCARE": "Medicare Benefits Growth Rate",
        "ABENMCAID": "Medicaid Benfits Growth Rate",
        "ABENSSI": "SSI Benefits Growth Rate",
        "ABENSNAP": "SNAP Benefits Growth Rate",
        "ABENWIC": "WIC Benfits Growth Rate",
        "ABENHOUSING": "Housing Benefits Growth Rate",
        "ABENTANF": "TANF Benfits Growth Rates",
        "ABENVET": "Veteran's Benfits Growth Rates",
    }
    if tb.params["growdiff_response"]:
        params = tb.params["growdiff_response"]
        growdiff_years = set()
        growdiff_by_year = defaultdict(lambda: deque())

        # base GrowFactor object to pull default values
        base_gf = tc.GrowFactors()
        # create GrowDiff and GrowFactors for the new assumptions
        reform_gd = tc.GrowDiff()
        reform_gd.update_growdiff(params)
        reform_gf = tc.GrowFactors()
        reform_gd.apply_to(reform_gf)
        # loop through all of the reforms
        for param, meta in params.items():
            # find all years a new value is specified
            years = set(meta.keys())
            growdiff_years = growdiff_years.union(years)
            name = growth_vars_map[param]
            for yr in years:
                # find default and new values
                default_val = base_gf.factor_value(param, yr)
                new_val = reform_gf.factor_value(param, yr)
                growdiff_by_year.append([name, default_val, new_val])

        # create tables
        md_tables = {}
        for yr in growdiff_years:
            content = growdiff_by_year[yr]
            content.appendleft(["", "Default Value", "New Value"])
            md_tables[yr] = convert_table(content)

        return md_tables

    else:
        return {"": "No new growth assumptions specified."}


def convert_params(params):
    """
    Convert ParamTools style parameter inputs to traditional taxcalc style
    parameters for report policy table creation

    Parameters
    ----------
    params: dict
        ParamTools style reform dictionary

    Returns
    -------
    reform: dict
        a dictionary in traditional taxcalc style
    """
    pol = tc.Policy()
    pol.adjust(params)
    indexed_params = []
    reform = defaultdict(dict)
    first_yr = pol.LAST_BUDGET_YEAR
    for param in params.keys():
        yrs = []
        if param.endswith("-indexed"):
            indexed_params.append(param)
            continue
        for adj in params[param]:
            yrs.append(adj["year"])
        yrs = set(yrs)
        values = getattr(pol, f"_{param}")
        for yr in yrs:
            idx = yr - pol.JSON_START_YEAR
            vals = values[idx]
            if isinstance(vals, np.ndarray):
                vals = list(vals)
            first_yr = min(yr, first_yr)
            reform[param][yr] = vals
    # add indexed parameters as being implemented in first year of reform
    for param in indexed_params:
        val = params[param][0]["value"]
        reform[param][first_yr] = val
    return reform


def dollar_str_formatting(val: Union[int, float]) -> str:
    """
    Format dollar figures into $val trillion, $val billion, etc.

    Parameters
    ----------
    val: float
        revenue amount

    Returns
    -------
    str
        formatted dollar figure
    """
    val = abs(val)
    if val >= 1e12:
        return f"{val * 1e-12:,.1f} trillion"
    elif 1e9 <= val < 1e12:
        return f"{val * 1e-9:,.1f} billion"
    elif 1e6 <= val < 1e9:
        return f"{val * 1e-6:,.1f} million"
    else:
        return f"{int(round(val, 0)):,}"
