import pytest
import pickle
from taxbrain.tbi import (run_tbi_model, summary_aggregate, summary_diff_xbin,
                          summary_diff_xdec, summary_dist_xbin,
                          summary_dist_xdec)


def test_tbi_model(empty_mods):
    """
    Test the run_tbi_model function
    """
    results = run_tbi_model(2018, "CPS", False, empty_mods)
    assert results.keys() == set(["outputs", "aggr_outputs"])
    assert len(results["outputs"]) == 10
    for i, result in enumerate(results["outputs"]):
        if not isinstance(results, dict):
            msg = (f"output result at index {i} is of type {type(result)}, ",
                   "not dict")
            raise TypeError(msg)
        expected_output_keys = ["tags", "dimension", "title", "downloadable",
                                "renderable"]
        assert list(result.keys()) == expected_output_keys
        assert isinstance(result["tags"], dict)
        assert isinstance(result["dimension"], int)
        assert isinstance(result["title"], str)
        assert isinstance(result["downloadable"], list)
        assert isinstance(result["renderable"], str)

    assert len(results["aggr_outputs"]) == 3
    for i, result in enumerate(results["aggr_outputs"]):
        if not isinstance(result, dict):
            msg = (f"aggr_outputs result at index {i} is of type ",
                   "{type(result}, not dict")
            raise TypeError(msg)


def test_table_functions(tb_static):
    """
    Test functions that produce the summary tables
    """
    res = {}
    # test summary_aggregate
    with pytest.raises(TypeError):
        summary_aggregate(list, tb_static)
    with pytest.raises(TypeError):
        summary_aggregate(res, list)
    expected_res_keys = ["aggr_d", "aggr_1", "aggr_2"]
    res = summary_aggregate(res, tb_static)
    assert list(res.keys()) == expected_res_keys

    # test summary_dist_xbin
    with pytest.raises(TypeError):
        summary_dist_xbin(list, tb_static, 2018)
    with pytest.raises(TypeError):
        summary_dist_xbin(res, list, 2018)
    with pytest.raises(TypeError):
        summary_dist_xbin(res, tb_static, "2018")
    expected_res_keys += ["dist1_xbin", "dist2_xbin"]
    res = summary_dist_xbin(res, tb_static, 2018)
    assert list(res.keys()) == expected_res_keys

    # test summary_diff_xbin
    with pytest.raises(TypeError):
        summary_diff_xbin(list, tb_static, 2018)
    with pytest.raises(TypeError):
        summary_diff_xbin(res, list, 2018)
    with pytest.raises(TypeError):
        summary_diff_xbin(res, tb_static, "2018")
    expected_res_keys += ["diff_itax_xbin", "diff_ptax_xbin", "diff_comb_xbin"]
    res = summary_diff_xbin(res, tb_static, 2018)
    assert list(res.keys()) == expected_res_keys

    # test summary_dist_xdec
    with pytest.raises(TypeError):
        summary_dist_xdec(list, tb_static, 2018)
    with pytest.raises(TypeError):
        summary_dist_xdec(res, list, 2018)
    with pytest.raises(TypeError):
        summary_dist_xdec(res, tb_static, "2018")
    expected_res_keys += ["dist1_xdec", "dist2_xdec"]
    res = summary_dist_xdec(res, tb_static, 2018)
    assert list(res.keys()) == expected_res_keys

    # test summary_diff_xdec
    with pytest.raises(TypeError):
        summary_diff_xdec(list, tb_static, 2018)
    with pytest.raises(TypeError):
        summary_diff_xdec(res, list, 2018)
    with pytest.raises(TypeError):
        summary_diff_xdec(res, tb_static, "2018")
    expected_res_keys += ["diff_itax_xdec", "diff_ptax_xdec", "diff_comb_xdec"]
    res = summary_diff_xdec(res, tb_static, 2018)
    assert list(res.keys()) == expected_res_keys
