import shutil
import os
from ogusa.execute import runner
from ogusa.utils import safe_read_pickle
from pathlib import Path


CUR_PATH = Path(__file__).resolve().parent
REFORM_DIR = Path(CUR_PATH, "ogusa_reform")
BASE_DIR = Path(CUR_PATH, "ogusa_baseline")


def run_ogusa(iit_base={}, iit_reform={}, og_spec_base={},
              og_spec_reform={}, data_source='cps', start_year=2021,
              num_years=10, client=None, num_workers=1):
    """
    Runs OG-USA model and returns percentage changes in macro variables
    used as growth factors for microdata.

    Parameters
    ----------
    iit_base: dict
        baseline policy for Tax-Calculator
    iit_reform: dict
        reform policy for Tax-Calculator
    og_spec_base: dict
        OG-USA specifications for the baseline simulation
    og_spec_reform: dict
        OG-USA specifications for the reform simulation
    data_source: str or Pandas DataFrame
        path or DataFrame of microdata to be used by Tax-Calculator
    start_year: int
        year to start simulations in
    num_years: int
        number of years over which to return the results
    client: Dask Client or None
        Dask client to use
    num_workers: int
        number of workers for parallelization

    Returns
    -------
    pct_w: Numpy array
        percentage changes in wages, starting from start_year going to
        start_year + num_years
    """

    '''
    ------------------------------------------------------------------------
    Run OG-USA baseline
    ------------------------------------------------------------------------
    '''
    og_spec_base['start_year'] = start_year
    og_spec_base['tax_func_type'] = 'GS'
    og_spec_base['age_specific'] = False
    kwargs = {'output_base': BASE_DIR, 'baseline_dir': BASE_DIR,
              'test': False, 'time_path': True, 'baseline': True,
              'og_spec': og_spec_base, 'guid': '',
              'iit_reform': iit_base,
              'run_micro': True, 'tax_func_path': None,
              'data': data_source, 'client': client,
              'num_workers': num_workers}
    runner(**kwargs)

    '''
    ------------------------------------------------------------------------
    Run reform policy
    ------------------------------------------------------------------------
    '''
    og_spec_reform['start_year'] = start_year
    og_spec_reform['tax_func_type'] = 'GS'
    og_spec_reform['age_specific'] = False
    kwargs = {'output_base': REFORM_DIR, 'baseline_dir': BASE_DIR,
              'test': False, 'time_path': True, 'baseline': False,
              'og_spec': og_spec_reform, 'guid': '',
              'iit_reform': iit_reform, 'run_micro': False,
              'tax_func_path': None, 'data': data_source,
              'client': client, 'num_workers': num_workers}
    runner(**kwargs)

    # return ans - the percentage changes in macro aggregates and prices
    # due to policy changes from the baseline to the reform
    base_tpi = safe_read_pickle(
        os.path.join(BASE_DIR, 'TPI', 'TPI_vars.pkl'))
    reform_tpi = safe_read_pickle(
        os.path.join(REFORM_DIR, 'TPI', 'TPI_vars.pkl'))

    # compute pct change in wages over first num_years
    pct_w = ((reform_tpi['w'] - base_tpi['w']) / base_tpi['w'])[:num_years]

    # remove newly created directories
    shutil.rmtree(BASE_DIR)
    shutil.rmtree(REFORM_DIR)

    return pct_w