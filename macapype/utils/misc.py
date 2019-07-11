def print_val(val):
    print(val)
    return val

def print_nii_data(nii_file):
    import nibabel as nib

    data = nib.load(nii_file).get_data()

    print (nii_file, data)

    return nii_file
