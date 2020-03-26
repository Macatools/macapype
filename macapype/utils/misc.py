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


def get_first_elem(elem):

    print(elem)
    if isinstance(elem, list):
        print("OK, is list")
        assert len(elem) == 1, "Error, list should contain only one element"
        return elem[0]
    else:
        print("not a list")
        return elem


def gunzip(filename):
    import subprocess

    if filename[-3:] == ".gz":
        subprocess.check_output("gunzip " + filename, shell=True)
    else:
        ValueError("Non GZip file given")
    return filename[:-3]

