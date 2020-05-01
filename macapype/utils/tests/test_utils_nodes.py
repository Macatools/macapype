import pytest
import os.path as op
from macapype.nodes.extract_brain import T1xT2BET

from macapype.utils.utils_tests import load_test_data

from macapype.utils.utils_nodes import NodeParams

data_path = load_test_data("data_test_macapype")

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
