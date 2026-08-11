import pytest
import os.path as op
from macapype.nodes.extract_brain import T1xT2BET

from macapype.utils.utils_tests import load_test_data
from macapype.utils.misc import parse_key

from macapype.utils.utils_nodes import NodeParams, MapNodeParams, ParseParams

from nipype.interfaces.base import traits
import nipype.interfaces.fsl as fsl

data_path = load_test_data("data_test_macaque")

T1_file = op.join(data_path, "sub-Apache_ses-01_T1w.nii")
T2_file = op.join(data_path, "sub-Apache_ses-01_T2w.nii")


def test_NodeParams_init():
    params = {"t_file": T1_file, "t2_file": T2_file, "aT2": True}
    with pytest.raises(AssertionError):
        bet_crop = NodeParams(interface=T1xT2BET(), params=params,  # noqa
                              name="bet_crop")


def test_NodeParams_load_inputs_from_dict():
    params = {"t_file": T1_file, "t2_file": T2_file, "aT2": True}
    bet_crop = NodeParams(interface=T1xT2BET(), name="bet_crop")
    with pytest.raises(AssertionError):
        bet_crop.load_inputs_from_dict(params)


def test_MapNodeParams():
    params = {"crop": {"args": "88 144 14 180 27 103"}}

    crop_bb = MapNodeParams(fsl.ExtractROI(), name='crop_bb',
                            params=parse_key(params, "crop"),
                            iterfield=["in_file"])

    crop_bb.inputs.in_file = [T1_file, T2_file]

    with pytest.raises(ValueError):
        crop_bb.run()


def test_ParseParams():
    params = {
        "sub-01": {
            "ses-01": {
                "node1": {
                    "arg": 1}}}}

    # should return non empty dict
    key = ("sub-01", "ses-01")
    val = ParseParams(params=params, key=key).run().outputs.parsed_params
    assert len(val) == 1

    # should return non empty dict
    key = "sub-01"
    val = ParseParams(params=params, key=key).run().outputs.parsed_params
    assert len(list(val.keys())) == 1

    # should return empty dict
    key = "sub-02"
    val = ParseParams(params=params, key=key).run().outputs.parsed_params
    assert len(val) == 0

    # should return empty dict
    key = "sub-01"
    params = traits.Undefined
    val = ParseParams(params=params, key=key).run().outputs.parsed_params
    assert len(val) == 0
