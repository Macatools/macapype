# on the fly function for checking what is passed in "connect"
# should end up in ~ nipype.utils.misc


def show_files(files):
    print(files)
    return files


def print_val(val):
    print(val)
    return val


def print_nii_data(nii_file):
    import nibabel as nib

    data = nib.load(nii_file).get_data()

    print(nii_file, data)

    return nii_file


def split_indexed_mask(nii_file, background_val=0):

    import os
    import nibabel as nib
    import numpy as np
    from nipype.utils.filemanip import split_filename as split_f

    path, fname, ext = split_f(nii_file)

    nii = nib.load(nii_file)

    nii_data = nii.get_data()

    list_split_files = []

    for index in np.unique(nii_data):
        if index == background_val:
            continue

        split_file = os.path.abspath("{}_{}{}".format(fname, index, ext))

        split_data = np.zeros(shape=nii_data.shape)
        split_data[nii_data == index] = 1

        nib.save(nib.Nifti1Image(split_data,
                                 header=nii.header,
                                 affine=nii.affine),
                 split_file)

        list_split_files.append(split_file)

    return list_split_files


def get_elem(list_elem, index_elem):
    assert isinstance(list_elem, list), 'Error, list_elem should be a list'
    assert 0 <= index_elem and index_elem <= len(list_elem),\
        ('error with index {}, does not match a list with {} elements'.format(
            index_elem, len(list_elem)))

    elem = list_elem[index_elem]
    print(elem)

    return elem


def get_first_elem(elem):
    print(elem)
    if isinstance(elem, list):
        print("OK, is list")
        assert len(elem) == 1, "Error, list should contain only one element"
        return elem[0]
    else:
        print("not a list")
        return elem


def gunzip(zipped_file):
    import subprocess
    import shutil
    import os

    head, tail = os.path.split(zipped_file)

    dest = os.path.abspath(tail)

    shutil.copy(zipped_file, dest)

    if zipped_file[-3:] == ".gz":
        subprocess.check_output("gunzip " + dest, shell=True)
    else:
        ValueError("Non GZip file given")

    print(os.listdir(os.path.abspath("")))

    unzipped_file = dest[:-3]
    return unzipped_file


def merge_3_elem_to_list(elem1, elem2, elem3):
    return [elem1, elem2, elem3]


def parse_key(params, key):

    from nipype.interfaces.base import isdefined

    def _parse_key(params, cur_key):
        if cur_key in params.keys():
            return params[cur_key]
        else:
            "Error, key {} was not found in {}".format(key, params.keys())
            return {}

    if isdefined(params):
        if isinstance(key, tuple):
            for cur_key in key:
                params = _parse_key(params, cur_key)
        else:
            params = _parse_key(params, key)

        return params

    else:
        return {}


def list_input_files(list_T1, list_T2):

    print("list_T1:", list_T1)
    print("list_T2:", list_T2)

    return ""
