# Write or import your COMP functions here.
import os
import json
import traceback
import paramtools
import pandas as pd
import taxcalc
import cs2tc
from .constants import MetaParameters
from .helpers import (TCDIR,
                      postprocess, nth_year_results, retrieve_puf,)
from .outputs import create_layout, aggregate_plot
from taxbrain import TaxBrain, report
from dask import delayed, compute
from collections import defaultdict, OrderedDict
from marshmallow import fields


AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

CUR_PATH = os.path.abspath(os.path.dirname(__file__))


class BehaviorParams(paramtools.Parameters):
    """
    Class for creating behavioral parameters
    """
    array_first = True
    with open(os.path.join(CUR_PATH, "behavior_params.json"), "r") as f:
        behavior_params = json.load(f)
    defaults = behavior_params


def get_version():
    model_versions_str = ""
    for model, version in TaxBrain.VERSIONS.items():
        model_versions_str += f"{model}: {version}\n"
    return model_versions_str


def get_inputs(meta_params_dict):
    """
    Return default parameters for Tax-Brain
    """
    meta_params = MetaParameters()
    with meta_params.transaction(defer_validation=True):
        meta_params.adjust(meta_params_dict)
        # Year must be at least 2014 when using the CPS. This rule is validated
        # in the validate_inputs function below.
        # See: https://github.com/PSLmodels/Tax-Brain/issues/176
        if meta_params.data_source == "CPS" and meta_params.year < 2014:
            meta_params.adjust({"year": 2014})

    policy_params = taxcalc.Policy()
    policy_params.set_state(year=meta_params.year.tolist())

    policy_defaults = cs2tc.convert_policy_defaults(meta_params, policy_params)

    behavior_params = BehaviorParams()

    default_params = {
        "policy": policy_defaults,
        "behavior": behavior_params.dump()
    }
    meta = meta_params.dump()

    return {"meta_parameters": meta, "model_parameters": default_params}


def validate_inputs(meta_params_dict, adjustment, errors_warnings):
    """
    Function to validate COMP inputs
    """
    meta_params = MetaParameters()
    meta_params.adjust(meta_params_dict, raise_errors=False)
    errors_warnings["policy"]["errors"].update(meta_params.errors)

    pol_params = cs2tc.convert_policy_adjustment(adjustment["policy"])
    policy_params = taxcalc.Policy()
    policy_params.adjust(pol_params, raise_errors=False, ignore_warnings=True)
    errors_warnings["policy"]["errors"].update(policy_params.errors)

    behavior_params = BehaviorParams()
    behavior_params.adjust(adjustment["behavior"], raise_errors=False)
    errors_warnings["behavior"]["errors"].update(behavior_params.errors)

    return {"errors_warnings": errors_warnings}


def run_model(meta_params_dict, adjustment):
    """
    Runs TaxBrain
    """
    # update meta parameters
    meta_params = MetaParameters()
    meta_params.adjust(meta_params_dict)
    # convert COMP user inputs to format accepted by tax-calculator
    policy_mods = cs2tc.convert_policy_adjustment(adjustment["policy"])
    behavior_mods = cs2tc.convert_behavior_adjustment(adjustment["behavior"])
    user_mods = {
        "policy": policy_mods,
        "behavior": behavior_mods
    }
    start_year = int(meta_params.year)
    use_cps = meta_params.data_source == "CPS"
    if meta_params.data_source == "PUF":
        puf_df = retrieve_puf(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        if puf_df is not None:
            if not isinstance(puf_df, pd.DataFrame):
                raise TypeError("'puf_df' must be a Pandas DataFrame.")
            fuzz = True
            use_cps = False
            sampling_frac = 0.05
            sampling_seed = 2222
            full_sample = puf_df
        else:
            # Access keys are not available. Default to the CPS.
            print("Defaulting to the CPS")
            meta_params.adjust({"data_source": "CPS"})
    if meta_params.data_source == "CPS":
        fuzz = False
        use_cps = True
        input_path = os.path.join(TCDIR, "cps.csv.gz")
        # full_sample = read_egg_csv(cpspath)  # pragma: no cover
        sampling_frac = 0.03
        sampling_seed = 180
        full_sample = pd.read_csv(input_path)

    if meta_params.use_full_sample:
        sample = full_sample
        end_year = min(start_year + 10, TaxBrain.LAST_BUDGET_YEAR)
    else:
        sample = full_sample.sample(frac=sampling_frac,
                                    random_state=sampling_seed)
        end_year = start_year

    tb = TaxBrain(start_year, end_year, microdata=sample,
                  use_cps=use_cps,
                  reform=policy_mods,
                  behavior=behavior_mods)
    tb.run()

    # Collect results for each year
    delayed_list = []
    for year in range(start_year, end_year + 1):
        print('delaying for', year)
        delay = delayed(nth_year_results)(tb, year, user_mods, fuzz)
        delayed_list.append(delay)
    results = compute(*delayed_list)

    # process results to get them ready for display
    # create aggregate plot
    agg_plot = aggregate_plot(tb)
    all_to_process = defaultdict(list)
    for result in results:
        for key, value in result.items():
            all_to_process[key] += value
    results, downloadable = postprocess(all_to_process)
    # create report output if it is not a run with no reforme
    if tb.params["policy"].keys():
        report_outputs = report(tb, clean=True)
        for name, data in report_outputs.items():
            if name.endswith(".md"):
                media_type = "Markdown"
            elif name.endswith(".pdf"):
                media_type = "PDF"
            downloadable.append(
                {
                    "media_type": media_type,
                    "title": name,
                    "data": data
                }
            )
    agg_output, table_output = create_layout(results, start_year, end_year)

    comp_outputs = {
        "renderable": [agg_plot, agg_output, table_output],
        "downloadable": downloadable
    }
    return comp_outputs
