
import os.path as op
from macapype.nodes.extract_brain import T1xT2BET

from macapype.utils.utils_tests import load_test_data
from macapype.utils.utils_nodes import NodeParams


def test_data_test_macaque():

    data_path = load_test_data("data_test_macaque")

    T1_file = op.join(data_path, "sub-Apache_ses-01_T1w.nii")
    T2_file = op.join(data_path, "sub-Apache_ses-01_T2w.nii")

    params = {"t1_file": T1_file, "t2_file": T2_file, "aT2": True}

    bet_crop = NodeParams(interface=T1xT2BET(), params=params,  # noqa
                          name="bet_crop")


def test_data_test_sphinx_macaque():

    data_path = load_test_data("data_test_sphinx_macaque")

    T1_file = op.join(data_path, "sub-ziggy_T1w.nii")
    T2_file = op.join(data_path, "sub-ziggy_T2w.nii")

    params = {"t1_file": T1_file, "t2_file": T2_file, "aT2": True}

    bet_crop = NodeParams(interface=T1xT2BET(), params=params,  # noqa
                          name="bet_crop")
