"""
Functions used to help tax-brain configure to COMP
"""
import os
import inspect
import time
import copy
import hashlib
import gzip
import copy
from pathlib import Path
import warnings

import pandas as pd
import numpy as np
from collections import defaultdict
from taxbrain.report_utils import convert_params
from taxcalc import (Policy, DIFF_TABLE_COLUMNS, DIFF_TABLE_LABELS,
                     DIST_TABLE_COLUMNS, DIST_TABLE_LABELS,
                     add_income_table_row_variable,
                     add_quantile_table_row_variable, STANDARD_INCOME_BINS)
from operator import itemgetter
from .constants import (POLICY_SCHEMA, RESULTS_TABLE_TAGS,
                        RESULTS_TABLE_TITLES, RESULTS_TOTAL_ROW_KEY_LABELS,
                        MONEY_VARS)
from .tables import (summary_aggregate, summary_diff_xbin, summary_diff_xdec,
                     summary_dist_xbin, summary_dist_xdec)

try:
    from s3fs import S3FileSystem
except ImportError as ie:
    S3FileSystem = None

TCPATH = inspect.getfile(Policy)
TCDIR = os.path.dirname(TCPATH)


AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", None)
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", None)


def random_seed(user_mods, year):
    """
    Compute random seed based on specified user_mods, which is a
    dictionary returned by Calculator.read_json_parameter_files().
    """
    def random_seed_from_subdict(subdict):
        """
        Compute random seed from one user_mods subdictionary.
        """
        assert isinstance(subdict, dict)
        all_vals = []
        for year in sorted(subdict.keys()):
            all_vals.append(str(year))
            params = subdict[year]
            for param in sorted(params.keys()):
                try:
                    tple = tuple(params[param])
                except TypeError:
                    # params[param] is not an iterable value; make it so
                    tple = tuple((params[param],))
                all_vals.append(str((param, tple)))
        txt = u''.join(all_vals).encode('utf-8')
        hsh = hashlib.sha512(txt)
        seed = int(hsh.hexdigest(), 16)
        return seed % np.iinfo(np.uint32).max
    # start of random_seed function
    # modify the user mods to work in the random_seed_from_subdict function
    # TODO: Change all of this to work with new adjustments
    user_mods_copy = copy.deepcopy(user_mods)
    beh_mods_dict = {year: {}}
    for param, value in user_mods_copy["behavior"].items():
        beh_mods_dict[year][param] = [value]
    user_mods_copy["behavior"] = beh_mods_dict
    ans = 0
    for subdict_name in user_mods_copy:
        subdict = user_mods_copy[subdict_name]
        if subdict_name == "policy":
            subdict = convert_params(subdict)
        ans += random_seed_from_subdict(subdict)
    return ans % np.iinfo(np.uint32).max


NUM_TO_FUZZ = 3  # when using dropq algorithm on puf.csv results


def fuzzed(df1, df2, reform_affected, table_row_type):
    """
    Create fuzzed df2 dataframe and corresponding unfuzzed df1 dataframe.

    Parameters
    ----------
    df1: Pandas DataFrame
        contains results variables for the baseline policy, which are not
        changed by this function

    df2: Pandas DataFrame
        contains results variables for the reform policy, which are not
        changed by this function

    reform_affected: boolean numpy array (not changed by this function)
        True for filing units with a reform-induced combined tax difference;
        otherwise False

    table_row_type: string
        valid values are 'aggr', 'xbin', and 'xdec'

    Returns
    -------
    df1, df2: Pandas DataFrames
        where copied df2 is fuzzed to maintain data privacy and
        where copied df1 has same filing unit order as has the fuzzed df2
    """
    assert table_row_type in ('aggr', 'xbin', 'xdec')
    assert len(df1.index) == len(df2.index)
    assert reform_affected.size == len(df1.index)
    df1 = copy.deepcopy(df1)
    df2 = copy.deepcopy(df2)
    # add copy of reform_affected to df2
    df2['reform_affected'] = copy.deepcopy(reform_affected)
    # construct table rows, for which filing units in each row must be fuzzed
    if table_row_type == 'xbin':
        df1 = add_income_table_row_variable(df1, 'expanded_income',
                                            STANDARD_INCOME_BINS)
        df2['expanded_income_baseline'] = df1['expanded_income']
        df2 = add_income_table_row_variable(df2, 'expanded_income_baseline',
                                            STANDARD_INCOME_BINS)
        del df2['expanded_income_baseline']
    elif table_row_type == 'xdec':
        df1 = add_quantile_table_row_variable(df1, 'expanded_income',
                                              10, decile_details=True)
        df2['expanded_income_baseline'] = df1['expanded_income']
        df2 = add_quantile_table_row_variable(df2, 'expanded_income_baseline',
                                              10, decile_details=True)
        del df2['expanded_income_baseline']
    elif table_row_type == 'aggr':
        df1['table_row'] = np.ones(reform_affected.shape, dtype=int)
        df2['table_row'] = df1['table_row']
    gdf1 = df1.groupby('table_row', sort=False)
    gdf2 = df2.groupby('table_row', sort=False)
    del df1['table_row']
    del df2['table_row']
    # fuzz up to NUM_TO_FUZZ filing units randomly chosen in each group
    # (or table row), where fuzz means to replace the reform (2) results
    # with the baseline (1) results for each chosen filing unit
    pd.options.mode.chained_assignment = None
    group_list = list()
    for name, group2 in gdf2:
        group2 = copy.deepcopy(group2)
        indices = np.where(group2['reform_affected'])
        num = min(len(indices[0]), NUM_TO_FUZZ)
        if num > 0:
            choices = np.random.choice(indices[0], size=num, replace=False)
            group1 = gdf1.get_group(name)
            for idx in choices:
                group2.iloc[idx] = group1.iloc[idx]
        group_list.append(group2)
        del group2
    df2 = pd.concat(group_list)
    del df2['reform_affected']
    pd.options.mode.chained_assignment = 'warn'
    # reinstate index order of df1 and df2 and return
    df1.sort_index(inplace=True)
    df2.sort_index(inplace=True)
    return (df1, df2)


def nth_year_results(tb, year, user_mods, fuzz, return_html=True):
    """
    Function to process taxbrain results for a given year
    """
    start_time = time.time()
    dv1 = tb.base_data[year]
    dv2 = tb.reform_data[year]
    sres = {}
    if fuzz:
        # seed random number generator with a seed value based on user_mods
        # (reform-specific seed is used to choose whose results are fuzzed)
        seed = random_seed(user_mods, year)
        np.random.seed(seed)
        # make bool array marking which filing units are affected by the reform
        reform_affected = np.logical_not(
            np.isclose(dv1['combined'], dv2['combined'], atol=0.01, rtol=0.0)
        )
        agg1, agg2 = fuzzed(dv1, dv2, reform_affected, 'aggr')
        sres = summary_aggregate(sres, tb)
        del agg1
        del agg2
        dv1b, dv2b = fuzzed(dv1, dv2, reform_affected, 'xbin')
        sres = summary_dist_xbin(sres, tb, year)
        sres = summary_diff_xbin(sres, tb, year)
        del dv1b
        del dv2b
        dv1d, dv2d = fuzzed(dv1, dv2, reform_affected, 'xdec')
        sres = summary_dist_xdec(sres, tb, year)
        sres = summary_diff_xdec(sres, tb, year)
        del dv1d
        del dv2d
        del reform_affected
    else:
        sres = summary_aggregate(sres, tb)
        sres = summary_dist_xbin(sres, tb, year)
        sres = summary_diff_xbin(sres, tb, year)
        sres = summary_dist_xdec(sres, tb, year)
        sres = summary_diff_xdec(sres, tb, year)

    # optionally return non-JSON-like results
    # it would be nice to allow the user to download the full CSV instead
    # of a CSV for each year
    # what if we allowed an aggregate format call?
    #  - presents project with all data proeduced in a run?

    if return_html:
        res = {}
        for id in sres:
            res[id] = [{
                'dimension': year,
                'raw': sres[id]
            }]
        elapsed_time = time.time() - start_time
        print('elapsed time for this run: {:.1f}'.format(elapsed_time))
        return res
    else:
        elapsed_time = time.time() - start_time
        print('elapsed time for this run: {:.1f}'.format(elapsed_time))
        return sres


def postprocess(data_to_process):
    """
    Receives results from run_nth_year_taxcalc_model over N years,
    formats the results, and combines the aggregate results
    """
    labels = {x: DIFF_TABLE_LABELS[i]
              for i, x in enumerate(DIFF_TABLE_COLUMNS)}
    labels.update({x: DIST_TABLE_LABELS[i]
                   for i, x in enumerate(DIST_TABLE_COLUMNS)})

    # nested functions used below
    def label_columns(pdf):
        pdf.columns = [(labels[str(col)] if str(col) in labels else str(col))
                       for col in pdf.columns]
        return pdf

    def append_year(pdf, year):
        """
        append_year embedded function revises all column names in dframe
        """
        pdf.columns = ['{}_{}'.format(col, year)
                       for col in pdf.columns]
        return pdf

    def year_columns(pdf, year):
        pdf.columns = [str(year)]
        return pdf

    def arbitrary_defaultdict():
        """
        Return an arbitrary number of defaultdicts. This is used to store all
        of the distribution and differences tables
        """
        return defaultdict(arbitrary_defaultdict)

    formatted = {"tbl_outputs": arbitrary_defaultdict(),
                 "aggr_outputs": defaultdict(dict)}
    downloadable = []
    year_getter = itemgetter('dimension')
    for id, pdfs in data_to_process.items():
        if id.startswith('aggr'):
            pdfs.sort(key=year_getter)
            tbl = pdfs[0]["raw"]
            tbl.index = pd.Index(RESULTS_TOTAL_ROW_KEY_LABELS[i]
                                 for i in tbl.index)
            # format table
            for col in tbl.columns:
                tbl.update(tbl[col].apply("${:,.2f}".format))

            title = RESULTS_TABLE_TITLES[id]
            tags = RESULTS_TABLE_TAGS[id]
            formatted["aggr_outputs"][tags["law"]] = {
                "title": title,
                "renderable": pdf_to_clean_html(tbl)
            }
            # append a downloadable version of the results
            downloadable.append(
                {
                    "media_type": "CSV",
                    "title": title + ".csv",
                    "data": tbl.to_csv()
                }
            )

        else:
            for i in pdfs:
                year = i["dimension"]
                tbl = label_columns(i["raw"])
                title = '{} ({})'.format(RESULTS_TABLE_TITLES[id],
                                         year)
                # format table
                for col in tbl.columns:
                    if col in MONEY_VARS:
                        tbl.update(tbl[col].apply("${:,.2f}".format))

                tags = RESULTS_TABLE_TAGS[id]
                tbl_type = tags["table_type"]
                group = tags["grouping"]
                if id.startswith("dist"):
                    law = tags["law"]
                    formatted["tbl_outputs"][tbl_type][law][group][year] = {
                            "title": title,
                            "renderable": pdf_to_clean_html(tbl)
                    }
                else:
                    tax = tags["tax_type"]
                    formatted["tbl_outputs"][tbl_type][tax][group][year] = {
                            "title": title,
                            "renderable": pdf_to_clean_html(tbl)
                    }

                # add downloadable information
                downloadable.append(
                    {
                        "media_type": "CSV",
                        "title": title + ".csv",
                        "data": tbl.to_csv()
                    }
                )

    return formatted, downloadable


def pdf_to_clean_html(pdf):
    """Takes a PDF and returns an HTML table without any deprecated tags or
    irrelevant styling"""
    tb_replace = ('<table class="table table-striped"')

    return (pdf.to_html()
            .replace('<table ', tb_replace)
            .replace(' border="1"', '')
            .replace('class="dataframe"', ''))


def retrieve_puf(
    aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY
):
    """
    Function for retrieving the PUF from the OSPC S3 bucket
    """
    s3_reader_installed = S3FileSystem is not None
    has_credentials = (
        aws_access_key_id is not None and aws_secret_access_key is not None
    )
    if has_credentials and s3_reader_installed:
        print("Reading puf from S3 bucket.")
        fs = S3FileSystem(key=AWS_ACCESS_KEY_ID, secret=AWS_SECRET_ACCESS_KEY,)
        with fs.open("s3://ospc-data-files/puf.csv.gz") as f:
            # Skips over header from top of file.
            puf_df = pd.read_csv(f, compression="gzip")
        return puf_df
    elif Path("puf.csv.gz").exists():
        print("Reading puf from puf.csv.gz.")
        return pd.read_csv("puf.csv.gz", compression="gzip")
    elif Path("puf.csv").exists():
        print("Reading puf from puf.csv.")
        return pd.read_csv("puf.csv")
    else:
        warnings.warn(
            f"PUF file not available (has_credentials={has_credentials}, "
            f"s3_reader_installed={s3_reader_installed})"
        )
        return None
