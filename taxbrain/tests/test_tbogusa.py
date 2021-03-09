import pytest
import multiprocessing
import time
from distributed import Client, LocalCluster
import taxbrain

NUM_WORKERS = min(multiprocessing.cpu_count(), 7)


@pytest.mark.local
def test_run_ogusa():
    base = {"II_em": {2019: 0}}
    reform = {"II_em": {2025: 2000}}
    p = multiprocessing.Process(
        target=taxbrain.tbogusa.run_ogusa, name="run_ogusa",
        args=(base, reform, {},
              {}, 'cps', 2019,
              10, None, NUM_WORKERS))
    p.start()
    time.sleep(300)
    if p.is_alive():
        p.terminate()
        p.join()
        timetest = True
    else:
        print("run_ogusa did not run for minimum time")
        timetest = False
    print('timetest ==', timetest)
