"""
The public API of the TaxBrain Interface (tbi) to Tax-Calculator, which can
be used by other models in the Policy Simulation Library (PSL) collection of
USA tax models.

The tbi functions are used by TaxBrain to call PSL tax models in order
to do distributed processing of TaxBrain runs and in order to maintain
the privacy of the IRS-SOI PUF data being used by TaxBrain.  Maintaining
privacy is done by "fuzzing" reform results for several randomly selected
filing units in each table cell.  The filing units randomly selected
differ for each policy reform and the "fuzzing" involves replacing the
post-reform tax results for the selected units with their pre-reform
tax results.
"""
# CODING-STYLE CHECKS:
# pycodestyle tbi.py
# pylint --disable=locally-disabled tbi.py

import os
import inspect
import copy
import hashlib
import time
import json
import numpy as np
import pandas as pd
from operator import itemgetter
from collections import defaultdict
from taxcalc import (Policy, Records, Calculator,
                     Consumption, GrowFactors, GrowDiff,
                     DIST_TABLE_LABELS, DIFF_TABLE_LABELS,
                     DIST_TABLE_COLUMNS, DIFF_TABLE_COLUMNS,
                     add_income_table_row_variable,
                     add_quantile_table_row_variable,
                     STANDARD_INCOME_BINS)
from taxbrain import TaxBrain
from dask import compute, delayed


CUR_PATH = os.path.abspath(os.path.dirname(__file__))
BEHV_PARAMS_PATH = os.path.join(CUR_PATH, "behavior_params.json")
with open(BEHV_PARAMS_PATH, "r") as f:
    BEHV_PARAMS = json.load(f)

AGG_ROW_NAMES = ['ind_tax', 'payroll_tax', 'combined_tax']

RESULTS_TABLE_TITLES = {
    'diff_comb_xbin': ('Combined Payroll and Individual Income Tax: Difference'
                       ' between Base and User plans by expanded income bin'),
    'diff_comb_xdec': ('Combined Payroll and Individual Income Tax: Difference'
                       ' between Base and User plans by expanded income '
                       'decile'),
    'diff_itax_xbin': ('Individual Income Tax: Difference between Base and '
                       'User plans by expanded income bin'),
    'diff_itax_xdec': ('Individual Income Tax: Difference between Base and '
                       'User plans by expanded income decile'),
    'diff_ptax_xbin': ('Payroll Tax: Difference between Base and User plans '
                       'by expanded income bin'),
    'diff_ptax_xdec': ('Payroll Tax: Difference between Base and User plans '
                       'by expanded income decile'),
    'dist1_xbin': 'Base plan tax vars, weighted total by expanded income bin',
    'dist1_xdec': ('Base plan tax vars, weighted total by expanded income '
                   'decile'),
    'dist2_xbin': 'User plan tax vars, weighted total by expanded income bin',
    'dist2_xdec': ('User plan tax vars, weighted total by expanded income '
                   'decile'),
    'aggr_1': 'Total Liabilities Baseline by Calendar Year (Billions)',
    'aggr_d': 'Total Liabilities Change by Calendar Year (Billions)',
    'aggr_2': 'Total Liabilities Reform by Calendar Year (Billions)'}

RESULTS_TABLE_TAGS = {
    # diff tables
    'diff_comb_xbin': {'table_type': 'diff', 'tax_type': 'combined',
                       'grouping': 'bins'},
    'diff_comb_xdec': {'table_type': 'diff', 'tax_type': 'combined',
                       'grouping': 'deciles'},
    'diff_itax_xbin': {'table_type': 'diff', 'tax_type': 'ind_income',
                       'grouping': 'bins'},
    'diff_itax_xdec': {'table_type': 'diff', 'tax_type': 'ind_income',
                       'grouping': 'deciles'},
    'diff_ptax_xbin': {'table_type': 'diff', 'tax_type': 'payroll',
                       'grouping': 'bins'},
    'diff_ptax_xdec': {'table_type': 'diff', 'tax_type': 'payroll',
                       'grouping': 'deciles'},
    # dist tables
    'dist1_xbin': {'table_type': 'dist', 'law': 'current',
                   'grouping': 'bins'},
    'dist1_xdec': {'table_type': 'dist', 'law': 'current',
                   'grouping': 'deciles'},
    'dist2_xbin': {'table_type': 'dist', 'law': 'reform',
                   'grouping': 'bins'},
    'dist2_xdec': {'table_type': 'dist', 'law': 'reform',
                   'grouping': 'deciles'},
    # aggr tables
    'aggr_1': {'law': 'current'},
    'aggr_d': {'law': 'change'},
    'aggr_2': {'law': 'reform'},
    # gdp elaticity model table
    'gdp_effect': {'default': 'gdp_elast'}
}
RESULTS_TOTAL_ROW_KEY_LABELS = {
    'ind_tax': 'Individual Income Tax Liability Change',
    'payroll_tax': 'Payroll Tax Liability Change',
    'combined_tax': ('Combined Payroll and Individual Income Tax Liability '
                     'Change'),
}


def get_defaults(start_year, **kwargs):
    pol = Policy()
    pol.set_year(start_year)
    pol_mdata = pol.metadata()
    # serialize taxcalc params
    seri = {}
    for param, data in pol_mdata.items():
        seri[param] = dict(data, **{"value": np.array(data["value"]).tolist()})

    return {"policy": seri, "behavior": BEHV_PARAMS}


def parse_user_inputs(params, jsonstrs, errors_warnings, data_source,
                      use_full_sample, start_year):
    """
    I've only sketched this code out. It has been run before, but only as a
    part of the taxcalcstyle comp package:
    https://github.com/comp-org/comp/blob/0.1.0rc7/webapp/apps/contrib/taxcalcstyle/parser.py
    """
    policy_inputs = params["policy"]
    behavior_inputs = params["behavior"]
    policy_inputs = {"policy": policy_inputs}
    policy_inputs_json = json.dumps(policy_inputs, indent=4)
    # format behavior inputs to work with behavior response function
    behavior_mods = {}
    for param, value in behavior_inputs.items():
        behavior_mods[param] = value[str(start_year)][0]
    behavior_inputs_json = json.dumps(behavior_mods, indent=4)

    assumption_inputs = {
        "growdiff_response": {},
        "consumption": {},
        "growdiff_baseline": {},
    }

    assumption_inputs_json = json.dumps(assumption_inputs, indent=4)

    policy_dict = Calculator.read_json_param_objects(
        policy_inputs_json, assumption_inputs_json
    )
    # get errors and warnings on parameters that do not cause ValueErrors
    tc_errors_warnings = reform_warnings_errors(
        policy_dict, data_source
    )
    behavior_errors = behavior_warnings_errors(behavior_mods, start_year)
    # errors_warnings contains warnings and errors separated by each
    # project/project module
    for project in tc_errors_warnings:
        errors_warnings[project] = parse_errors_warnings(
            tc_errors_warnings[project]
        )
    errors_warnings["behavior"]["errors"] = behavior_errors

    # separate reform and assumptions
    reform_dict = policy_dict["policy"]
    assumptions_dict = {
        k: v for k, v in list(policy_dict.items()) if k != "policy"
    }

    params = {"policy": reform_dict, "behavior": behavior_mods,
              **assumptions_dict}
    # print('\np', params)
    jsonstrs = {"policy": policy_inputs_json,
                "assumptions": assumption_inputs_json,
                "behavior": behavior_inputs_json}

    return (
        params,
        jsonstrs,
        errors_warnings,
    )


def parse_errors_warnings(errors_warnings):
    """
    Parse error messages so that they can be mapped to webapp param ID. This
    allows the messages to be displayed under the field where the value is
    entered.

    returns: dictionary 'parsed' with keys: 'errors' and 'warnings'
        parsed['errors/warnings'] = {year: {tb_param_name: 'error message'}}
    """
    parsed = {"errors": defaultdict(dict), "warnings": defaultdict(dict)}
    for action in errors_warnings:
        msgs = errors_warnings[action]
        if len(msgs) == 0:
            continue
        for msg in msgs.split("\n"):
            if len(msg) == 0:  # new line
                continue
            msg_spl = msg.split()
            msg_action = msg_spl[0]
            year = msg_spl[1]
            curr_id = msg_spl[2]
            msg_parse = msg_spl[2:]
            parsed[action][curr_id][year] = " ".join(
                [msg_action] + msg_parse + ["for", year]
            )
    return parsed


def reform_warnings_errors(user_mods, data_source):
    """
    The reform_warnings_errors function assumes user_mods is a dictionary
    returned by the Calculator.read_json_param_objects() function.

    This function returns a dictionary containing five STR:STR subdictionaries,
    where the dictionary keys are: 'policy', 'behavior', consumption',
    'growdiff_baseline' and 'growdiff_response'; and the subdictionaries are:
    {'warnings': '<empty-or-message(s)>', 'errors': '<empty-or-message(s)>'}.
    Note that non-policy parameters have no warnings, so the 'warnings'
    string for the non-policy parameters is always empty.
    """
    using_puf = data_source == "PUF"
    rtn_dict = {'policy': {'warnings': '', 'errors': ''},
                'consumption': {'warnings': '', 'errors': ''},
                'growdiff_baseline': {'warnings': '', 'errors': ''},
                'growdiff_response': {'warnings': '', 'errors': ''}}
    # create GrowDiff objects
    gdiff_baseline = GrowDiff()
    try:
        gdiff_baseline.update_growdiff(user_mods['growdiff_baseline'])
    except ValueError as valerr_msg:
        rtn_dict['growdiff_baseline']['errors'] = valerr_msg.__str__()
    gdiff_response = GrowDiff()
    try:
        gdiff_response.update_growdiff(user_mods['growdiff_response'])
    except ValueError as valerr_msg:
        rtn_dict['growdiff_response']['errors'] = valerr_msg.__str__()
    # create Growfactors object
    growfactors = GrowFactors()
    gdiff_baseline.apply_to(growfactors)
    gdiff_response.apply_to(growfactors)
    # create Policy object
    pol = Policy(gfactors=growfactors)
    try:
        pol.implement_reform(user_mods['policy'],
                             print_warnings=False,
                             raise_errors=False)
        if using_puf:
            rtn_dict['policy']['warnings'] = pol.parameter_warnings
        rtn_dict['policy']['errors'] = pol.parameter_errors
    except ValueError as valerr_msg:
        rtn_dict['policy']['errors'] = valerr_msg.__str__()

    # create Consumption object
    consump = Consumption()
    try:
        consump.update_consumption(user_mods['consumption'])
    except ValueError as valerr_msg:
        rtn_dict['consumption']['errors'] = valerr_msg.__str__()
    # return composite dictionary of warnings/errors
    return rtn_dict


def behavior_warnings_errors(behavior_mods, year):
    """
    This function analyzes the behavior_mods dictionary to ensure that the
    value of each input meets the requirements for being used by the
    Behavioral-Reponses package
    """
    err_str_template = "{} must be between {} and {}\n"
    err_dict = {}
    for mod, value in behavior_mods.items():
        min_val = BEHV_PARAMS[mod]["validators"]["range"]["min"]
        max_val = BEHV_PARAMS[mod]["validators"]["range"]["max"]
        if not min_val <= value <= max_val:
            # err_str += err_str_template.format(mod, min_val, max_val)
            err_dict[mod] = {year: err_str_template.format(mod, min_val,
                                                           max_val)}
    return err_dict


def pdf_to_clean_html(pdf):
    """Takes a PDF and returns an HTML table without any deprecated tags or
    irrelevant styling"""
    return (pdf.to_html()
            .replace(' border="1"', '')
            .replace(' style="text-align: right;"', ''))


def run_tbi_model(start_year, data_source, use_full_sample, user_mods,
                  puf_df=None):
    """
    Run TBI using the taxbrain API
    """
    tbi_path = os.path.abspath(os.path.dirname(__file__))
    tcpath = inspect.getfile(Records)
    tcdir = os.path.dirname(tcpath)
    # use taxbrain
    if data_source == "PUF":
        if not isinstance(puf_df, pd.DataFrame):
            raise TypeError("'puf_df' must be a Pandas DataFrame.")
        fuzz = True
        use_cps = False
        sampling_frac = 0.05
        sampling_seed = 2222
        full_sample = puf_df
    else:
        fuzz = False
        use_cps = True
        input_path = os.path.join(tbi_path, '..', 'cps.csv.gz')
        if not os.path.isfile(input_path):
            # otherwise read from taxcalc package "egg"
            input_path = os.path.join(tcdir, "cps.csv.gz")
            # full_sample = read_egg_csv(cpspath)  # pragma: no cover
        sampling_frac = 0.03
        sampling_seed = 180
        full_sample = pd.read_csv(input_path)

    if use_full_sample:
        sample = full_sample
        end_year = min(start_year + 10, TaxBrain.LAST_BUDGET_YEAR)
    else:
        sample = full_sample.sample(frac=sampling_frac,
                                    random_state=sampling_seed)
        end_year = start_year

    tb = TaxBrain(start_year, end_year, microdata=sample, use_cps=use_cps,
                  reform=user_mods["policy"], behavior=user_mods["behavior"])
    tb.run()

    # Collect results for each year
    delayed_list = []
    for year in range(start_year, end_year + 1):
        print('delaying for', year)
        delay = delayed(nth_year_results)(tb, year, user_mods, fuzz)
        delayed_list.append(delay)
    results = compute(*delayed_list)

    all_to_process = defaultdict(list)
    for result in results:
        for key, value in result.items():
            all_to_process[key] += value
    results = postprocess(all_to_process)
    return results


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
        print('fuzzing_seed={}'.format(seed))
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
                'raw': sres[id].to_json()
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
              for i, x in enumerate(DIFF_TABLE_COLUMNS[:-2])}
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

    formatted = {'outputs': [], 'aggr_outputs': []}
    year_getter = itemgetter('dimension')
    for id, pdfs in data_to_process.items():
        if id.startswith('aggr'):
            pdfs.sort(key=year_getter)
            tbl = pd.read_json(pdfs[0]["raw"])
            tbl.index = pd.Index(RESULTS_TOTAL_ROW_KEY_LABELS[i]
                                 for i in tbl.index)
            title = RESULTS_TABLE_TITLES[id]
            formatted['aggr_outputs'].append({
                'tags': RESULTS_TABLE_TAGS[id],
                'title': title,
                'downloadable': [{'filename': title + '.csv',
                                  'text': tbl.to_csv()}],
                'renderable': pdf_to_clean_html(tbl)
            })
        else:
            for i in pdfs:
                tbl = label_columns(pd.read_json(i['raw']))
                title = '{} ({})'.format(RESULTS_TABLE_TITLES[id],
                                         i['dimension'])
                formatted['outputs'].append({
                    'tags': RESULTS_TABLE_TAGS[id],
                    'dimension': i['dimension'],
                    'title': title,
                    'downloadable': [{'filename': title + '.csv',
                                      'text': tbl.to_csv()}],
                    'renderable': pdf_to_clean_html(tbl)
                })
    return formatted

# -------------------------------------------------------
# Begin "private" functions used to build functions like
# run_nth_year_taxcalc_model for other models in the USA
# tax collection of the Policy Simulation Library (PSL).
# Any other use of the following functions is suspect.
# -------------------------------------------------------


def check_years(year_n, start_year, use_puf_not_cps):
    """
    Ensure year_n and start_year values are valid given input data used.
    """
    if year_n < 0:
        msg = 'year_n={} < 0'
        raise ValueError(msg.format(year_n))
    if use_puf_not_cps:
        first_data_year = Records.PUFCSV_YEAR
    else:
        first_data_year = Records.CPSCSV_YEAR
    first_year = max(Policy.JSON_START_YEAR, first_data_year)
    if start_year < first_year:
        msg = 'start_year={} < first_year={}'
        raise ValueError(msg.format(start_year, first_year))
    if (start_year + year_n) > Policy.LAST_BUDGET_YEAR:
        msg = '(start_year={} + year_n={}) > Policy.LAST_BUDGET_YEAR={}'
        raise ValueError(msg.format(start_year, year_n,
                                    Policy.LAST_BUDGET_YEAR))


def check_user_mods(user_mods):
    """
    Ensure specified user_mods is properly structured.
    """
    if not isinstance(user_mods, dict):
        raise ValueError('user_mods is not a dictionary')
    actual_keys = set(list(user_mods.keys()))
    expected_keys = set(['policy', 'consumption',
                         'growdiff_baseline', 'growdiff_response', 'behavior'])
    if actual_keys != expected_keys:
        msg = 'actual user_mod keys not equal to expected keys\n'
        msg += '  actual: {}\n'.format(actual_keys)
        msg += '  expect: {}'.format(expected_keys)
        raise ValueError(msg)


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
    user_mods_copy = copy.deepcopy(user_mods)
    beh_mods_dict = {year: {}}
    for param, value in user_mods_copy["behavior"].items():
        beh_mods_dict[year][param] = [value]
    user_mods_copy["behavior"] = beh_mods_dict
    ans = 0
    for subdict_name in user_mods_copy:
        ans += random_seed_from_subdict(user_mods_copy[subdict_name])
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
        indices = np.where(group2['reform_affected'])
        num = min(len(indices[0]), NUM_TO_FUZZ)
        if num > 0:
            choices = np.random.choice(indices[0], size=num, replace=False)
            group1 = gdf1.get_group(name)
            for idx in choices:
                group2.iloc[idx] = group1.iloc[idx]
        group_list.append(group2)
    df2 = pd.concat(group_list)
    del df2['reform_affected']
    pd.options.mode.chained_assignment = 'warn'
    # reinstate index order of df1 and df2 and return
    df1.sort_index(inplace=True)
    df2.sort_index(inplace=True)
    return (df1, df2)


def summary_aggregate(res, tb):
    """
    Function to produce aggregate revenue tables
    """
    if not isinstance(res, dict):
        raise TypeError(
            f"'res' is of type {type(res)}. Must be dictionary object."
        )
    if not isinstance(tb, TaxBrain):
        raise TypeError(
            f"'tb' is of type {type(tb)}. Must be TaxBrain object"
        )
    # tax totals for baseline
    tax_vars = ["iitax", "payrolltax", "combined"]
    aggr_base = tb.multi_var_table(tax_vars, "base")
    aggr_base.index = AGG_ROW_NAMES
    # tax totals for reform
    aggr_reform = tb.multi_var_table(tax_vars, "reform")
    aggr_reform.index = AGG_ROW_NAMES
    # tax difference
    aggr_d = aggr_reform - aggr_base
    # add to dictionary
    res["aggr_d"] = (aggr_d / 1e9).round(3)
    res["aggr_1"] = (aggr_base / 1e9).round(3)
    res["aggr_2"] = (aggr_reform / 1e9).round(3)
    del aggr_base, aggr_reform, aggr_d
    return res


def summary_dist_xbin(res, tb, year):
    """
    res is dictionary of summary-results DataFrames.
    df1 contains results variables for baseline policy.
    df2 contains results variables for reform policy.
    returns augmented dictionary of summary-results DataFrames.
    """
    if not isinstance(res, dict):
        raise TypeError(
            f"'res' is of type {type(res)}. Must be dictionary object."
        )
    if not isinstance(tb, TaxBrain):
        raise TypeError(
            f"'tb' is of type {type(tb)}. Must be TaxBrain object"
        )
    if not isinstance(year, int):
        raise TypeError(
            f"'year' is of type {type(year)}. Must be an integer"
        )
    # create distribution tables grouped by xbin
    # baseline distribution table
    res["dist1_xbin"] = tb.distribution_table(year, "standard_income_bins",
                                              "expanded_income", "base")
    # reform distribution table
    # ensure income is grouped on the same measure
    expanded_income_baseline = tb.base_data[year]["expanded_income"]
    tb.reform_data[year]["expanded_income_baseline"] = expanded_income_baseline
    res["dist2_xbin"] = tb.distribution_table(year, "standard_income_bins",
                                              "expanded_income_baseline",
                                              "reform")
    del tb.reform_data[year]["expanded_income_baseline"]
    return res


def summary_diff_xbin(res, tb, year):
    """
    res is dictionary of summary-results DataFrames.
    df1 contains results variables for baseline policy.
    df2 contains results variables for reform policy.
    returns augmented dictionary of summary-results DataFrames.
    """
    if not isinstance(res, dict):
        raise TypeError(
            f"'res' is of type {type(res)}. Must be dictionary object."
        )
    if not isinstance(tb, TaxBrain):
        raise TypeError(
            f"'tb' is of type {type(tb)}. Must be TaxBrain object"
        )
    if not isinstance(year, int):
        raise TypeError(
            f"'year' is of type {type(year)}. Must be an integer"
        )
    # create difference tables grouped by xbin
    res["diff_itax_xbin"] = tb.differences_table(year, "standard_income_bins",
                                                 "iitax")
    res["diff_ptax_xbin"] = tb.differences_table(year, "standard_income_bins",
                                                 "payrolltax")
    res["diff_comb_xbin"] = tb.differences_table(year, "standard_income_bins",
                                                 "combined")
    return res


def summary_dist_xdec(res, tb, year):
    """
    res is dictionary of summary-results DataFrames.
    df1 contains results variables for baseline policy.
    df2 contains results variables for reform policy.
    returns augmented dictionary of summary-results DataFrames.
    """
    if not isinstance(res, dict):
        raise TypeError(
            f"'res' is of type {type(res)}. Must be dictionary object."
        )
    if not isinstance(tb, TaxBrain):
        raise TypeError(
            f"'tb' is of type {type(tb)}. Must be TaxBrain object"
        )
    if not isinstance(year, int):
        raise TypeError(
            f"'year' is of type {type(year)}. Must be an integer"
        )
    # create distribution tables grouped by xdec
    res["dist1_xdec"] = tb.distribution_table(year, "weighted_deciles",
                                              "expanded_income", "base")
    # reform distribution table
    # ensure income is grouped on the same measure
    expanded_income_baseline = tb.base_data[year]["expanded_income"]
    tb.reform_data[year]["expanded_income_baseline"] = expanded_income_baseline
    res["dist2_xdec"] = tb.distribution_table(year, "weighted_deciles",
                                              "expanded_income_baseline",
                                              "reform")
    del tb.reform_data[year]["expanded_income_baseline"]
    return res


def summary_diff_xdec(res, tb, year):
    """
    res is dictionary of summary-results DataFrames.
    df1 contains results variables for baseline policy.
    df2 contains results variables for reform policy.
    returns augmented dictionary of summary-results DataFrames.
    """
    if not isinstance(res, dict):
        raise TypeError(
            f"'res' is of type {type(res)}. Must be dictionary object."
        )
    if not isinstance(tb, TaxBrain):
        raise TypeError(
            f"'tb' is of type {type(tb)}. Must be TaxBrain object"
        )
    if not isinstance(year, int):
        raise TypeError(
            f"'year' is of type {type(year)}. Must be an integer"
        )
    # create difference tables grouped by xdec
    res["diff_itax_xdec"] = tb.differences_table(year, "weighted_deciles",
                                                 "iitax")
    res["diff_ptax_xdec"] = tb.differences_table(year, "weighted_deciles",
                                                 "payrolltax")
    res["diff_comb_xdec"] = tb.differences_table(year, "weighted_deciles",
                                                 "combined")
    return res
