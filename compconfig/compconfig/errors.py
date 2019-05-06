"""
Functions for error handling in COMP
"""
import os
import json
from collections import defaultdict
from taxcalc import Policy, GrowDiff, GrowFactors, Consumption


CUR_PATH = os.path.abspath(os.path.dirname(__file__))
BEHV_PARAMS_PATH = os.path.join(CUR_PATH, "behavior_params.json")
with open(BEHV_PARAMS_PATH, "r") as f:
    BEHV_PARAMS = json.load(f)


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
