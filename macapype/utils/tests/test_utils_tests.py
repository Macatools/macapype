import os
import shutil

import os.path as op

import pytest

from macapype.nodes.extract_brain import T1xT2BET

from macapype.utils.utils_tests import (load_test_data, format_template,
                                        make_tmp_dir)
from macapype.utils.utils_nodes import NodeParams


def test_server_amubox():
    tmp_path = make_tmp_dir()
    name = op.join(tmp_path, "data_test_macaque.zip")

    code = "RDxdxzmX89xcABG"
    server = "https://amubox.univ-amu.fr"
    add = "{}/public.php?service=files&t={}&download".format(server, code)
    cmd = "wget  --no-check-certificate  \"{}\" -O {}".format(add, name)

    os.system(cmd)


def test_load_test_data():
    with pytest.raises(AssertionError):
        load_test_data("do_not_exists")


def test_load_test_data_dataset():

    template_name = "NMT_v2.0_asym"
    nmt_dir = load_test_data(name=template_name)
    params_template = format_template(nmt_dir, template_name)

    assert len(params_template) != 0


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


def test_zenodo_server():

    test_file = "Juna_Chimp_T1_1mm_skull.nii.gz"
    download_file = os.path.abspath(test_file)

    os.system("wget --no-check-certificate  --content-disposition \
        https://zenodo.org/record/4683381/files/{}?download=1 \
        -O {}".format(test_file, download_file))

    assert os.path.exists(download_file)

    os.remove(download_file)


def test_load_test_data_zenodo():

    tmp_path = make_tmp_dir()
    name = "Juna_Chimp"
    data_path = load_test_data(name=name, path_to=tmp_path)

    print(data_path)

    assert os.path.exists(data_path)
    assert len(os.listdir(data_path))

    shutil.rmtree(data_path)


if __name__ == '__main__':

    # test_load_test_data()
    # test_data_test_macaque()

    test_zenodo_server()
    test_load_test_data_zenodo()
