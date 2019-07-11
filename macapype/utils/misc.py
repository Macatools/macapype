#### on the fly function for checking what is passed in "connect"
#### should end up in ~ nipype.utils.misc

def show_files(files):
    print(files)
    return files

def print_val(val):
    print(val)
    return val

def print_nii_data(nii_file):
    import nibabel as nib

    data = nib.load(nii_file).get_data()

    print (nii_file, data)

    return nii_file
