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


def get_elem(list_elem, index_elem):
    assert isinstance(list_elem, list), 'Error, list_elem should be a list'
    assert 0 <= index_elem and index_elem <= len(list_elem),\
        ('error with index {}, does not match a list with {} elements'.format(
            index_elem, len(list_elem)))

    elem = list_elem[index_elem]
    print(elem)

    return elem


def get_pattern(list_elem, pattern):

    assert isinstance(list_elem, list), 'Error, list_elem should be a list'

    for elem in list_elem:
        if pattern in elem:
            print("Found {} in {}".format(pattern, elem))
            return elem

    assert False, "Could not find {} in {}".format(pattern, elem)


def get_list_length(list_elem):
    assert isinstance(list_elem, list), 'Error, list_elem should be a list'
    return len(list_elem)


def get_first_elem(elem):
    print(elem)
    if isinstance(elem, list):
        print("OK, is list")
        assert len(elem) == 1, "Error, list should contain only one element"
        return elem[0]
    else:
        print("not a list")
        return elem


def gzip(unzipped_file):

    import os
    import shutil
    import subprocess

    head, tail = os.path.split(unzipped_file)

    dest = os.path.abspath(tail)

    print("Copying {} to {}".format(unzipped_file, dest))
    shutil.copy(unzipped_file, dest)
    cmd_line = "gzip {}".format(dest)

    subprocess.check_output(cmd_line, shell=True)

    zipped_file = dest + ".gz"

    assert os.path.exists(zipped_file),\
        "Error, {} should exists".format(zipped_file)

    return zipped_file


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
