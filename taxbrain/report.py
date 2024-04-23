import shutil
import pandas as pd
import behresp
import taxbrain
import taxcalc as tc
from pathlib import Path
from .report_utils import (
    form_intro,
    form_baseline_intro,
    write_text,
    date,
    largest_tax_change,
    notable_changes,
    behavioral_assumptions,
    consumption_assumptions,
    policy_table,
    convert_table,
    growth_assumptions,
    md_to_pdf,
    DIFF_TABLE_ROW_NAMES,
    dollar_str_formatting,
)


CUR_PATH = Path(__file__).resolve().parent


def report(
    tb,
    name=None,
    change_threshold=0.05,
    description=None,
    outdir=None,
    author="",
    css=None,
    verbose=False,
    clean=False,
):
    """
    Create a PDF report based on TaxBrain results

    Parameters
    ----------
    tb: TaxBrain object
        instance of a TaxBrain object
    name: str
        Name you want used for the title of the report
    change_threshold: float
        Percentage change (expressed as a decimal fraction) in
        an aggregate variable for it to be considered notable
    description: str
        A description of the reform being run
    outdir: str
        Output directory
    author: str
        Person or persons to be listed as the author of the report
    css: str
        Path to a CSS file used to format the final report
    verbose: bool
        boolean indicating whether or not to write progress as report is
        created
    clean: bool
        boolean indicating whether all of the files written to create the
        report should be deleated and a byte representation of the PDF returned

    Returns
    --------
    files or None: dict or None
        returns either None (reports saved to disk) or dictionary with
        string of bytes for markdown and pdf versions of the report

    """

    def format_table(df, int_cols, float_cols, float_perc=2):
        """
        Apply formatting to a given table

        Parameters
        ----------
        df: Pandas DataFrame
            DataFrame being formatted
        int_cols: list
            columns that need to be converted to integers
        float_cols: list
            floatcolumns that need to be converted to floats
        float_perc: int
            Decimal percision for float columns the table. Default is 2

        Returns
        --------
        df: Pandas DataFrame
            table of output
        """
        for col in int_cols:
            df.update(df[col].astype(int).apply("{:,}".format))
        for col in float_cols:
            df.update(
                df[col]
                .astype(float)
                .apply("{:,.{}}".format, args=(float_perc,))
            )
        return df

    def export_plot(plot, graph):
        """
        Export plot as a PNG

        Parameters
        -----------
        plot: Matplolib.pyplot plot object
            plot to export
        graph: str
            str to use in file name of plot to save

        Returns
        -------
        str
            full filename indicating where plot is saved
        """
        # export graph as a PNG
        # we could get a higher quality image with an SVG, but the SVG plots
        # do not render correctly in the PDF document
        filename = f"{graph}_graph.png"
        full_filename = Path(output_path, filename)
        plot.savefig(full_filename, dpi=1200, bbox_inches="tight")

        return str(full_filename)

    if not tb.has_run:
        tb.run()
    if not name:
        name = f"Policy Report-{date()}"
    if not outdir:
        outdir = name.replace(" ", "_")
    if author:
        author = f"Report Prepared by {author.title()}"
    # create directory to hold report contents
    output_path = Path(outdir)
    if not output_path.exists():
        output_path.mkdir()
    # dictionary to hold pieces of the final text
    text_args = {
        "start_year": tb.start_year,
        "end_year": tb.end_year,
        "title": name,
        "date": date(),
        "author": author,
        "taxbrain": str(Path(CUR_PATH, "report_files", "taxbrain.png")),
    }
    if tb.stacked:
        stacked_table = tb.stacked_table * 1e-9
        stacked_table = format_table(
            stacked_table, [], list(stacked_table.columns), float_perc=1
        )
        stacked_table = convert_table(stacked_table)
        text_args["stacked_table"] = stacked_table
    if verbose:
        print("Writing Introduction")
    # find policy areas used in the reform
    pol = tc.Policy()
    pol_meta = pol.metadata()
    pol_areas = set()
    for var in tb.params["policy"].keys():
        # catch "{}-indexed" parameter changes
        if "-" in var:
            var = var.split("-")[0]
        area = pol_meta[var]["section_1"].lower()
        if area == "social security taxability":
            area = "Social Security taxability"
        if area != "":
            pol_areas.add(area)
    pol_areas = list(pol_areas)
    # add policy areas to the intro text
    text_args["introduction"] = form_intro(pol_areas, description)
    # write final sentance of introduction
    current_law = tb.params["base_policy"]
    text_args["baseline_intro"] = form_baseline_intro(current_law)

    if verbose:
        print("Writing Summary")
    agg_table = tb.weighted_totals("combined", include_total=True).fillna(0)
    rev_change = agg_table.loc["Difference"].sum()
    rev_direction = "increase"
    if rev_change < 0:
        rev_direction = "decrease"
    text_args["rev_direction"] = rev_direction
    text_args["rev_change"] = dollar_str_formatting(rev_change)

    # create differences table
    if verbose:
        print("Creating differences table")
    diff_table = tb.differences_table(
        tb.start_year, "standard_income_bins", "combined"
    ).fillna(0)
    diff_table.index = DIFF_TABLE_ROW_NAMES

    decile_diff_table = tb.differences_table(
        tb.start_year, "weighted_deciles", "combined"
    ).fillna(0)
    # move the "ALL" row to the bottom of the DataFrame
    target_row = decile_diff_table.loc["ALL", :]
    decile_diff_table = decile_diff_table.shift(-1)
    decile_diff_table.iloc[-1] = target_row.squeeze()

    # find which income bin sees the largest change in tax liability
    largest_change = largest_tax_change(diff_table)
    text_args["largest_change_group"] = largest_change[0]
    text_args["largest_change_str"] = largest_change[1]
    decile_diff_table.columns = tc.DIFF_TABLE_LABELS
    # drop certain columns to save space
    if tc.__version__ >= "3.2.1":
        drop_cols = [
            "Share of Overall Change",
            "Number of Returns with Tax Cut",
            "Number of Returns with Tax Increase",
        ]
    else:
        drop_cols = [
            "Share of Overall Change",
            "Count with Tax Cut",
            "Count with Tax Increase",
        ]
    sub_diff_table = decile_diff_table.drop(columns=drop_cols)

    # convert DataFrame to Markdown table
    sub_diff_table.index.name = "_Income &nbsp; Decile_"
    diff_table = format_table(sub_diff_table, [], list(sub_diff_table.columns))
    diff_md = convert_table(diff_table)
    text_args["differences_table"] = diff_md

    # aggregate results
    if verbose:
        print("Compiling aggregate results")
    # format aggregate table
    agg_table *= 1e-9
    agg_table = format_table(agg_table, list(agg_table.columns), [])
    agg_md = convert_table(agg_table)
    text_args["agg_table"] = agg_md

    # aggregate table by tax type
    tax_vars = ["iitax", "payrolltax", "combined"]
    agg_base = tb.multi_var_table(tax_vars, "base", include_total=True)
    agg_reform = tb.multi_var_table(tax_vars, "reform", include_total=True)
    agg_diff = agg_reform - agg_base
    agg_diff.index = ["Income Tax", "Payroll Tax", "Combined"]
    agg_diff *= 1e-9
    agg_diff = format_table(agg_diff, list(agg_diff.columns), [])
    text_args["agg_tax_type"] = convert_table(agg_diff)

    # summary of policy changes
    text_args["reform_summary"] = policy_table(tb.params["policy"])

    # policy baseline
    if tb.params["base_policy"]:
        text_args["policy_baseline"] = policy_table(tb.params["base_policy"])
    else:
        text_args["policy_baseline"] = (
            f"This report is based on current law as of {date()}."
        )

    # notable changes
    if verbose:
        print("Finding notable changes")
    text_args["notable_changes"] = notable_changes(tb, change_threshold)

    # behavioral assumptions
    if verbose:
        print("Compiling assumptions")
    text_args["behavior_assumps"] = behavioral_assumptions(tb)
    # consumption asssumptions
    text_args["consump_assumps"] = consumption_assumptions(tb)
    # growth assumptions
    text_args["growth_assumps"] = growth_assumptions(tb)

    # determine model versions
    text_args["model_versions"] = [
        {"name": "Tax-Brain", "release": taxbrain.__version__},
        {"name": "Tax-Calculator", "release": tc.__version__},
        {"name": "Behavioral-Responses", "release": behresp.__version__},
    ]

    # create graphs
    if verbose:
        print("Creating graphs")
    dist_graph = taxbrain.distribution_plot(
        tb,
        tb.start_year,
        (5, 4),
        f"Fig. 2: Percentage Change in After-Tax Income - {tb.start_year}",
    )
    text_args["distribution_graph"] = export_plot(dist_graph, "dist")

    # differences graph
    diff_graph = taxbrain.differences_plot(
        tb,
        "combined",
        (6, 3),
        title="Fig. 1: Change in Aggregate Combined Tax Liability",
    )
    text_args["agg_graph"] = export_plot(diff_graph, "difference")

    # fill in the report template
    if verbose:
        print("Compiling report")
    template_path = Path(CUR_PATH, "report_files", "report_template.md")
    report_md = write_text(template_path, **text_args)

    # write PDF, markdown files
    filename = name.replace(" ", "-")
    pdf_path = Path(output_path, f"{filename}.pdf")
    md_path = Path(output_path, f"{filename}.md")
    md_path.write_text(report_md)
    md_to_pdf(report_md, str(pdf_path))

    if clean:
        # return PDF as bytes and the markdown text
        byte_pdf = pdf_path.read_bytes()
        files = {f"{filename}.md": report_md, f"{filename}.pdf": byte_pdf}
        # remove directory where everything was saved
        shutil.rmtree(output_path)
        assert not output_path.exists()
        return files
