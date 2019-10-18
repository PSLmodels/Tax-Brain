# Write or import your COMP functions here.
import os
import json
import traceback
import paramtools
import pandas as pd
from .constants import MetaParameters
from .helpers import (convert_defaults, convert_adj, TCDIR,
                      postprocess, nth_year_results, retrieve_puf,
                      convert_behavior_adj)
from .outputs import create_layout, aggregate_plot
from taxbrain import TaxBrain
from dask import delayed, compute
from collections import defaultdict
from marshmallow import fields
from collections import OrderedDict


AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

with open(os.path.join(TCDIR, "policy_current_law.json"), "r") as f:
    pcl = json.loads(f.read())

RES = convert_defaults(pcl)
CUR_PATH = os.path.abspath(os.path.dirname(__file__))


class TCParams(paramtools.Parameters):
    defaults = RES
    label_to_extend = "year"


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
    metaparams = MetaParameters()
    metaparams.adjust(meta_params_dict)

    policy_params = TCParams()
    policy_params.set_state(
        year=metaparams.year.tolist(),
        data_source=metaparams.data_source,
    )

    filtered_pol_params = OrderedDict()
    for k, v in policy_params.dump().items():
        if k =="schema" or v.get("section_1", False):
            filtered_pol_params[k] = v

    behavior_params = BehaviorParams()

    default_params = {
        "policy": filtered_pol_params,
        "behavior": behavior_params.dump()
    }
    meta = metaparams.dump()

    return {"meta_parameters": meta, "model_parameters": default_params}


def validate_inputs(meta_params_dict, adjustment, errors_warnings):
    """
    Function to validate COMP inputs
    """
    pol_params = {}
    # drop checkbox parameters.
    for param, data in list(adjustment["policy"].items()):
        if not param.endswith("checkbox"):
            pol_params[param] = data

    policy_params = TCParams()
    policy_params.adjust(pol_params, raise_errors=False)
    errors_warnings["policy"]["errors"].update(policy_params.errors)

    behavior_params = BehaviorParams()
    behavior_params.adjust(adjustment["behavior"], raise_errors=False)
    errors_warnings["behavior"]["errors"].update(behavior_params.errors)

    if policy_params.errors or behavior_params.errors:
        return {"errors_warnings": errors_warnings}

    # try to parse to the correct Tax-Calculator format.
    try:
        # update meta parameters
        meta_params = MetaParameters()
        meta_params.adjust(meta_params_dict)

        tc_adj = {
            "policy": convert_adj(adjustment["policy"],
                                  meta_params.year.tolist()),
            "behavior": convert_behavior_adj(adjustment["behavior"])
        }
        res = {"errors_warnings": errors_warnings, "custom_adjustment": tc_adj}
    except Exception:
        res = {"errors_warnings": errors_warnings}
        print("Error parsing:", adjustment)
        traceback.print_exc()

    return res


def run_model(meta_params_dict, adjustment):
    """
    Runs TaxBrain
    """
    # update meta parameters
    meta_params = MetaParameters()
    meta_params.adjust(meta_params_dict)
    # convert COMP user inputs to format accepted by tax-calculator
    policy_mods = convert_adj(adjustment["policy"], meta_params.year.tolist())
    behavior_mods = convert_behavior_adj(adjustment["behavior"])
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
    agg_output, table_output = create_layout(results, start_year, end_year)

    comp_outputs = {
        "renderable": [agg_plot, agg_output, table_output],
        "downloadable": downloadable
    }
    return comp_outputs
