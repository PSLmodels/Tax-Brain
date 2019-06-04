import numpy as np
from dask.distributed import Client
from ogusa import postprocess
from ogusa.execute import runner
from pathlib import Path


CUR_PATH = Path(__file__).resolve().parent
REFORM_DIR = Path(CUR_PATH, "ogusa_reform")
BASE_DIR = Path(CUR_PATH, "ogusa_baseline")


def run_ogusa(micro_reform, data_source, start_year):
    """
    Run OG-USA Model
    Parameters
    ----------
    user_params: User params for OG-USA
    micro_reform: Tax poilcy reform
    """
    client = Client(processes=False)
    num_workers = 1
    # pass in OG-USA arguments
    # og_args = {
    #     "output_base": REFORM_DIR, "baseline_dir": BASE_DIR, "test": False,
    #     "time_path": True, "baseline": False, "user_params": user_params,
    #     "guid": "_example", "reform": micro_reform, "run_micro": True,
    #     "data": data_source, "client": client, "num_workers": num_workers
    # }
    # temporarily use default user params
    alpha_T = np.zeros(50)
    alpha_T[0:2] = 0.09
    alpha_T[2:10] = 0.09 + 0.01
    alpha_T[10:40] = 0.09 - 0.01
    alpha_T[40:] = 0.09
    alpha_G = np.zeros(7)
    alpha_G[0:3] = 0.05 - 0.01
    alpha_G[3:6] = 0.05 - 0.005
    alpha_G[6:] = 0.05
    small_open = False
    user_params = {'frisch': 0.41, 'start_year': start_year,
                   'tau_b': [(0.35 * 0.55) * (0.017 / 0.055)],
                   'debt_ratio_ss': 1.0, 'alpha_T': alpha_T.tolist(),
                   'alpha_G': alpha_G.tolist(), 'small_open': small_open}
    og_args = {
        "output_base": REFORM_DIR, "baseline_dir": BASE_DIR,
        "test": False, "time_path": True, "baseline": False,
        "user_params": user_params, "guid": "_example",
        "reform": micro_reform, "run_micro": True, "data": "cps",
        "client": client, "num_workers": num_workers
    }
    print("running")
    runner(**og_args)

    # compare reform results and baseline
    ans = postprocess.create_diff(
        baseline_dir=BASE_DIR, policy_dir=REFORM_DIR
    )

    return ans
