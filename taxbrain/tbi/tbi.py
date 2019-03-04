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
from behresp import PARAM_INFO, response
from taxcalc import (Policy, Records, Calculator,
                     Consumption, GrowFactors, GrowDiff,
                     DIST_TABLE_LABELS, DIFF_TABLE_LABELS,
                     DIST_TABLE_COLUMNS, DIFF_TABLE_COLUMNS,
                     add_income_table_row_variable,
                     add_quantile_table_row_variable,
                     create_difference_table, create_distribution_table,
                     STANDARD_INCOME_BINS, read_egg_csv)

AGG_ROW_NAMES = ['ind_tax', 'payroll_tax', 'combined_tax']

GDP_ELAST_ROW_NAMES = ['gdp_proportional_change']

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
    'aggr_1': 'Total Liabilities Baseline by Calendar Year',
    'aggr_d': 'Total Liabilities Change by Calendar Year',
    'aggr_2': 'Total Liabilities Reform by Calendar Year'}

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
RESULTS_TABLE_ELAST_TITLES = {
    'gdp_effect': 'Percentage Change in GDP'
}
RESULTS_TOTAL_ELAST_ROW_KEY_LABELS = {
    'gdp_effect': '% Difference in GDP'
}


def get_defaults(start_year, **kwargs):
    pol = Policy()
    pol.set_year(start_year)
    pol_mdata = pol.metadata()
    behv_mdata = {}
    for param, meta in PARAM_INFO.items():
        behv_mdata[param] = {
            "title": meta["long_name"],
            "description": meta["description"],
            "section_1": "Behavior",
            "section_2": "",
            "notes": "",
            "type": 'float',
            'value': [meta['default_value']],
            'validators': {
                'range': {'min': meta['minimum_value'],
                          'max': meta['maximum_value']}
            },
            'boolean_value': False,
            'integer_value': False
        }

    return {"policy": pol_mdata, "behavior": behv_mdata}


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
    if behavior_inputs:
        for param, value in behavior_inputs.items():
            for year, val in value.items():
                int_year = int(year)
                if int_year not in behavior_mods.keys():
                    behavior_mods[int_year] = {param: val[0]}
                else:
                    behavior_mods[int_year][param] = val[0]
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
    # errors_warnings contains warnings and errors separated by each
    # project/project module
    for project in tc_errors_warnings:
        errors_warnings[project] = parse_errors_warnings(
            tc_errors_warnings[project]
        )

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
    # # create Behavior object
    # behv = Behavior()
    # try:
    #     behv.update_behavior(user_mods['behavior'])
    # except ValueError as valerr_msg:
    #     rtn_dict['behavior']['errors'] = valerr_msg.__str__()
    # create Consumption object
    consump = Consumption()
    try:
        consump.update_consumption(user_mods['consumption'])
    except ValueError as valerr_msg:
        rtn_dict['consumption']['errors'] = valerr_msg.__str__()
    # return composite dictionary of warnings/errors
    return rtn_dict


def pdf_to_clean_html(pdf):
    """Takes a PDF and returns an HTML table without any deprecated tags or
    irrelevant styling"""
    return (pdf.to_html()
            .replace(' border="1"', '')
            .replace(' style="text-align: right;"', ''))


def run_tbi_model(start_year, data_source, use_full_sample, user_mods):
    """
    Main function for running the Drop-Q model.
    """
    results = []
    if use_full_sample:
        num_years = 10
    else:
        num_years = 1
    for i in range(0, num_years):
        results.append(
            run_nth_year_taxcalc_model(
                year_n=i,
                data_source=data_source,
                start_year=start_year,
                use_full_sample=use_full_sample,
                user_mods=user_mods,
            )
        )
    all_to_process = defaultdict(list)
    for result in results:
        for key, value in result.items():
            all_to_process[key] += value
    results = postprocess(all_to_process)
    return results


def run_nth_year_taxcalc_model(year_n,
                               start_year,
                               data_source,
                               use_full_sample,
                               user_mods,
                               return_html=True):
    """
    The run_nth_year_taxcalc_model function assumes user_mods is a dictionary
      returned by the Calculator.read_json_param_objects() function.
    Setting use_puf_not_cps=True implies use puf.csv input file;
      otherwise, use cps.csv input file.
    Setting use_full_sample=False implies use sub-sample of input file;
      otherwsie, use the complete sample.
    """
    # pylint: disable=too-many-arguments,too-many-statements
    # pylint: disable=too-many-locals,too-many-branches

    use_puf_not_cps = data_source == "PUF"
    start_time = time.time()
    # create calc1 and calc2 calculated for year_n
    check_years(year_n, start_year, use_puf_not_cps)
    calc1, calc2 = calculator_objects(year_n, start_year,
                                      use_puf_not_cps, use_full_sample,
                                      user_mods)

    # extract unfuzzed raw results from calc1 and calc2
    # run dynamic response if user specified a behavior modification
    if user_mods["behavior"]:
        print("Dynamic!!")
        dv1, dv2 = response(calc1, calc2, user_mods["behavior"])
    else:
        # otherwise simply extract the distribution tables
        dv1 = calc1.distribution_table_dataframe()
        dv2 = calc2.distribution_table_dataframe()

    # delete calc1 and calc2 now that raw results have been extracted
    del calc1
    del calc2

    # construct TaxBrain summary results from raw results
    sres = dict()
    fuzzing = use_puf_not_cps
    if fuzzing:
        # seed random number generator with a seed value based on user_mods
        # (reform-specific seed is used to choose whose results are fuzzed)
        seed = random_seed(user_mods)
        print('fuzzing_seed={}'.format(seed))
        np.random.seed(seed)
        # make bool array marking which filing units are affected by the reform
        reform_affected = np.logical_not(
            np.isclose(dv1['combined'], dv2['combined'], atol=0.01, rtol=0.0)
        )
        agg1, agg2 = fuzzed(dv1, dv2, reform_affected, 'aggr')
        sres = summary_aggregate(sres, agg1, agg2)
        del agg1
        del agg2
        dv1b, dv2b = fuzzed(dv1, dv2, reform_affected, 'xbin')
        sres = summary_dist_xbin(sres, dv1b, dv2b)
        sres = summary_diff_xbin(sres, dv1b, dv2b)
        del dv1b
        del dv2b
        dv1d, dv2d = fuzzed(dv1, dv2, reform_affected, 'xdec')
        sres = summary_dist_xdec(sres, dv1d, dv2d)
        sres = summary_diff_xdec(sres, dv1d, dv2d)
        del dv1d
        del dv2d
        del reform_affected
    else:
        sres = summary_aggregate(sres, dv1, dv2)
        sres = summary_dist_xbin(sres, dv1, dv2)
        sres = summary_diff_xbin(sres, dv1, dv2)
        sres = summary_dist_xdec(sres, dv1, dv2)
        sres = summary_diff_xdec(sres, dv1, dv2)

    # optionally return non-JSON-like results
    # it would be nice to allow the user to download the full CSV instead
    # of a CSV for each year
    # what if we allowed an aggregate format call?
    #  - presents project with all data proeduced in a run?

    if return_html:
        res = {}
        for id in sres:
            res[id] = [{
                'dimension': start_year + year_n,
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
            tbl = pd.concat((year_columns(pd.read_json(i['raw']),
                                          i['dimension'])
                             for i in pdfs), axis='columns')
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


def calculator_objects(year_n, start_year,
                       use_puf_not_cps,
                       use_full_sample,
                       user_mods,):
    """
    This function assumes that the specified user_mods is a dictionary
      returned by the Calculator.read_json_param_objects() function.
    This function returns (calc1, calc2) where
      calc1 is pre-reform Calculator object calculated for year_n, and
      calc2 is post-reform Calculator object calculated for year_n.
    """
    # pylint: disable=too-many-arguments,too-many-locals
    # pylint: disable=too-many-branches,too-many-statements

    check_user_mods(user_mods)

    # specify Consumption instance
    consump = Consumption()
    consump_assumptions = user_mods['consumption']
    consump.update_consumption(consump_assumptions)

    # specify growdiff_baseline and growdiff_response
    growdiff_baseline = GrowDiff()
    growdiff_response = GrowDiff()
    growdiff_base_assumps = user_mods['growdiff_baseline']
    growdiff_resp_assumps = user_mods['growdiff_response']
    growdiff_baseline.update_growdiff(growdiff_base_assumps)
    growdiff_response.update_growdiff(growdiff_resp_assumps)

    # create pre-reform and post-reform GrowFactors instances
    growfactors_pre = GrowFactors()
    growdiff_baseline.apply_to(growfactors_pre)
    growfactors_post = GrowFactors()
    growdiff_baseline.apply_to(growfactors_post)
    growdiff_response.apply_to(growfactors_post)

    # create sample pd.DataFrame from specified input file and sampling scheme
    tbi_path = os.path.abspath(os.path.dirname(__file__))
    tcpath = inspect.getfile(Records)
    tcdir = os.path.dirname(tcpath)
    if use_puf_not_cps:
        # first try TaxBrain deployment path
        input_path = 'puf.csv.gz'
        if not os.path.isfile(input_path):
            # otherwise try local Tax-Calculator deployment path
            input_path = os.path.join(tbi_path, '..', '..', 'puf.csv')
        sampling_frac = 0.05
        sampling_seed = 2222
    else:  # if using cps input not puf input
        # first try Tax-Calculator code path
        input_path = os.path.join(tbi_path, '..', 'cps.csv.gz')
        if not os.path.isfile(input_path):
            # otherwise read from taxcalc package "egg"
            input_path = None  # pragma: no cover
            cpspath = os.path.join(tcdir, "cps.csv.gz")
            # full_sample = read_egg_csv(cpspath)  # pragma: no cover
            full_sample = pd.read_csv(cpspath)
        sampling_frac = 0.03
        sampling_seed = 180
    if input_path:
        full_sample = pd.read_csv(input_path)
    if use_full_sample:
        sample = full_sample
    else:
        sample = full_sample.sample(frac=sampling_frac,
                                    random_state=sampling_seed)

    # create pre-reform Calculator instance
    if use_puf_not_cps:
        recs1 = Records(data=sample,
                        gfactors=growfactors_pre)
    else:
        recs1 = Records.cps_constructor(data=sample,
                                        gfactors=growfactors_pre)
    policy1 = Policy(gfactors=growfactors_pre)
    calc1 = Calculator(policy=policy1, records=recs1, consumption=consump)
    while calc1.current_year < start_year:
        calc1.increment_year()
    calc1.calc_all()
    assert calc1.current_year == start_year

    # create post-reform Calculator instance
    if use_puf_not_cps:
        recs2 = Records(data=sample,
                        gfactors=growfactors_post)
    else:
        recs2 = Records.cps_constructor(data=sample,
                                        gfactors=growfactors_post)
    policy2 = Policy(gfactors=growfactors_post)
    policy_reform = user_mods['policy']
    policy2.implement_reform(policy_reform)
    calc2 = Calculator(policy=policy2, records=recs2,
                       consumption=consump)
    while calc2.current_year < start_year:
        calc2.increment_year()
    assert calc2.current_year == start_year

    # delete objects now embedded in calc1 and calc2
    del sample
    del full_sample
    del consump
    del growdiff_baseline
    del growdiff_response
    del growfactors_pre
    del growfactors_post
    del recs1
    del recs2
    del policy1
    del policy2

    # increment Calculator objects for year_n years and calculate
    for _ in range(0, year_n):
        calc1.increment_year()
        calc2.increment_year()
    calc1.calc_all()
    calc2.calc_all()

    # return calculated Calculator objects
    return (calc1, calc2)


def calculators(year_n, start_year,
                use_puf_not_cps,
                use_full_sample,
                user_mods):
    """
    This function assumes that the specified user_mods is a dictionary
      returned by the Calculator.read_json_param_objects() function.
    This function returns (calc1, calc2) where
      calc1 is pre-reform Calculator object for year_n, and
      calc2 is post-reform Calculator object for year_n.
    Neither Calculator object has had the calc_all() method executed.
    """
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    print('\nc', user_mods)

    check_user_mods(user_mods)

    # specify Consumption instance
    consump = Consumption()
    consump_assumptions = user_mods['consumption']
    consump.update_consumption(consump_assumptions)

    # specify growdiff_baseline and growdiff_response
    growdiff_baseline = GrowDiff()
    growdiff_response = GrowDiff()
    growdiff_base_assumps = user_mods['growdiff_baseline']
    growdiff_resp_assumps = user_mods['growdiff_response']
    growdiff_baseline.update_growdiff(growdiff_base_assumps)
    growdiff_response.update_growdiff(growdiff_resp_assumps)

    # create pre-reform and post-reform GrowFactors instances
    growfactors_pre = GrowFactors()
    growdiff_baseline.apply_to(growfactors_pre)
    growfactors_post = GrowFactors()
    growdiff_baseline.apply_to(growfactors_post)
    growdiff_response.apply_to(growfactors_post)

    # create sample pd.DataFrame from specified input file and sampling scheme
    tbi_path = os.path.abspath(os.path.dirname(__file__))
    if use_puf_not_cps:
        # first try TaxBrain deployment path
        input_path = 'puf.csv.gz'
        if not os.path.isfile(input_path):
            # otherwise try local Tax-Calculator deployment path
            input_path = os.path.join(tbi_path, '..', '..', 'puf.csv')
        sampling_frac = 0.05
        sampling_seed = 2222
    else:  # if using cps input not puf input
        # first try Tax-Calculator code path
        input_path = os.path.join(tbi_path, '..', 'cps.csv.gz')
        if not os.path.isfile(input_path):
            # otherwise read from taxcalc package "egg"
            input_path = None  # pragma: no cover
            full_sample = read_egg_csv('cps.csv.gz')  # pragma: no cover
        sampling_frac = 0.03
        sampling_seed = 180
    if input_path:
        full_sample = pd.read_csv(input_path)
    if use_full_sample:
        sample = full_sample
    else:
        sample = full_sample.sample(frac=sampling_frac,
                                    random_state=sampling_seed)

    # create pre-reform Calculator instance
    if use_puf_not_cps:
        recs1 = Records(data=sample,
                        gfactors=growfactors_pre)
    else:
        recs1 = Records.cps_constructor(data=sample,
                                        gfactors=growfactors_pre)
    policy1 = Policy(gfactors=growfactors_pre)
    calc1 = Calculator(policy=policy1, records=recs1, consumption=consump)
    while calc1.current_year < start_year:
        calc1.increment_year()
    assert calc1.current_year == start_year

    # create post-reform Calculator instance
    if use_puf_not_cps:
        recs2 = Records(data=sample,
                        gfactors=growfactors_post)
    else:
        recs2 = Records.cps_constructor(data=sample,
                                        gfactors=growfactors_post)
    policy2 = Policy(gfactors=growfactors_post)
    policy_reform = user_mods['policy']
    policy2.implement_reform(policy_reform)
    calc2 = Calculator(policy=policy2, records=recs2, consumption=consump)
    while calc2.current_year < start_year:
        calc2.increment_year()
    assert calc2.current_year == start_year

    # delete objects now embedded in calc1 and calc2
    del sample
    del full_sample
    del consump
    del growdiff_baseline
    del growdiff_response
    del growfactors_pre
    del growfactors_post
    del recs1
    del recs2
    del policy1
    del policy2

    # increment Calculator objects for year_n years
    for _ in range(0, year_n):
        calc1.increment_year()
        calc2.increment_year()

    # return Calculator objects
    return (calc1, calc2)


def random_seed(user_mods):
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
    ans = 0
    for subdict_name in user_mods:
        ans += random_seed_from_subdict(user_mods[subdict_name])
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


def summary_aggregate(res, df1, df2):
    """
    res is dictionary of summary-results DataFrames.
    df1 contains results variables for baseline policy.
    df2 contains results variables for reform policy.
    returns augmented dictionary of summary-results DataFrames.
    """
    # pylint: disable=too-many-locals
    # tax difference totals between reform and baseline
    aggr_itax_d = ((df2['iitax'] - df1['iitax']) * df2['s006']).sum()
    aggr_ptax_d = ((df2['payrolltax'] - df1['payrolltax']) * df2['s006']).sum()
    aggr_comb_d = ((df2['combined'] - df1['combined']) * df2['s006']).sum()
    aggrd = [aggr_itax_d, aggr_ptax_d, aggr_comb_d]
    res['aggr_d'] = pd.DataFrame(data=aggrd, index=AGG_ROW_NAMES)
    del aggrd
    # tax totals for baseline
    aggr_itax_1 = (df1['iitax'] * df1['s006']).sum()
    aggr_ptax_1 = (df1['payrolltax'] * df1['s006']).sum()
    aggr_comb_1 = (df1['combined'] * df1['s006']).sum()
    aggr1 = [aggr_itax_1, aggr_ptax_1, aggr_comb_1]
    res['aggr_1'] = pd.DataFrame(data=aggr1, index=AGG_ROW_NAMES)
    del aggr1
    # tax totals for reform
    aggr_itax_2 = (df2['iitax'] * df2['s006']).sum()
    aggr_ptax_2 = (df2['payrolltax'] * df2['s006']).sum()
    aggr_comb_2 = (df2['combined'] * df2['s006']).sum()
    aggr2 = [aggr_itax_2, aggr_ptax_2, aggr_comb_2]
    res['aggr_2'] = pd.DataFrame(data=aggr2, index=AGG_ROW_NAMES)
    del aggr2
    # scale res dictionary elements
    for tbl in ['aggr_d', 'aggr_1', 'aggr_2']:
        for col in res[tbl]:
            res[tbl][col] = round(res[tbl][col] * 1.e-9, 3)
    # return res dictionary
    return res


def summary_dist_xbin(res, df1, df2):
    """
    res is dictionary of summary-results DataFrames.
    df1 contains results variables for baseline policy.
    df2 contains results variables for reform policy.
    returns augmented dictionary of summary-results DataFrames.
    """
    # create distribution tables grouped by xbin
    res['dist1_xbin'] = \
        create_distribution_table(df1, 'standard_income_bins',
                                  'expanded_income')
    df2['expanded_income_baseline'] = df1['expanded_income']
    res['dist2_xbin'] = \
        create_distribution_table(df2, 'standard_income_bins',
                                  'expanded_income_baseline')
    del df2['expanded_income_baseline']
    # return res dictionary
    return res


def summary_diff_xbin(res, df1, df2):
    """
    res is dictionary of summary-results DataFrames.
    df1 contains results variables for baseline policy.
    df2 contains results variables for reform policy.
    returns augmented dictionary of summary-results DataFrames.
    """
    # create difference tables grouped by xbin
    res['diff_itax_xbin'] = \
        create_difference_table(df1, df2, 'standard_income_bins', 'iitax')
    res['diff_ptax_xbin'] = \
        create_difference_table(df1, df2, 'standard_income_bins', 'payrolltax')
    res['diff_comb_xbin'] = \
        create_difference_table(df1, df2, 'standard_income_bins', 'combined')
    # return res dictionary
    return res


def summary_dist_xdec(res, df1, df2):
    """
    res is dictionary of summary-results DataFrames.
    df1 contains results variables for baseline policy.
    df2 contains results variables for reform policy.
    returns augmented dictionary of summary-results DataFrames.
    """
    # create distribution tables grouped by xdec
    res['dist1_xdec'] = \
        create_distribution_table(df1, 'weighted_deciles',
                                  'expanded_income')
    df2['expanded_income_baseline'] = df1['expanded_income']
    res['dist2_xdec'] = \
        create_distribution_table(df2, 'weighted_deciles',
                                  'expanded_income_baseline')
    del df2['expanded_income_baseline']
    # return res dictionary
    return res


def summary_diff_xdec(res, df1, df2):
    """
    res is dictionary of summary-results DataFrames.
    df1 contains results variables for baseline policy.
    df2 contains results variables for reform policy.
    returns augmented dictionary of summary-results DataFrames.
    """
    # create difference tables grouped by xdec
    res['diff_itax_xdec'] = \
        create_difference_table(df1, df2, 'weighted_deciles', 'iitax')
    res['diff_ptax_xdec'] = \
        create_difference_table(df1, df2, 'weighted_deciles', 'payrolltax')
    res['diff_comb_xdec'] = \
        create_difference_table(df1, df2, 'weighted_deciles', 'combined')
    # return res dictionary
    return res


def create_dict_table(dframe, row_names=None, column_types=None,
                      num_decimals=2):
    """
    Create and return dictionary with JSON-like content from specified dframe.
    """
    # embedded formatted_string function
    def formatted_string(val, _type, num_decimals):
        """
        Return formatted conversion of number val into a string.
        """
        float_types = [float, np.dtype('f8')]
        int_types = [int, np.dtype('i8')]
        frmat_str = "0:.{num}f".format(num=num_decimals)
        frmat_str = "{" + frmat_str + "}"
        try:
            if _type in float_types or _type is None:
                return frmat_str.format(val)
            if _type in int_types:
                return str(int(val))
            if _type == str:
                return str(val)
            raise NotImplementedError()
        except ValueError:
            # try making it a string - good luck!
            return str(val)
    # high-level create_dict_table function logic
    out = dict()
    if row_names is None:
        row_names = [str(x) for x in list(dframe.index)]
    else:
        assert len(row_names) == len(dframe.index)
    if column_types is None:
        column_types = [dframe[col].dtype for col in dframe.columns]
    else:
        assert len(column_types) == len(dframe.columns)
    for idx, row_name in zip(dframe.index, row_names):
        row_out = out.get(row_name, [])
        for col, dtype in zip(dframe.columns, column_types):
            row_out.append(formatted_string(dframe.loc[idx, col],
                                            dtype, num_decimals))
        out[row_name] = row_out
    return out


def check_years_return_first_year(year_n, start_year, use_puf_not_cps):
    """
    Ensure year_n and start_year values are valid given input data used.
    Return value of first year, which is maximum of first records data year
    and first policy parameter year.
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
    return first_year
