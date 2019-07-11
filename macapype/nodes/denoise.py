
def nonlocal_denoise(img_file, params = [3,1,1], method = "aonlm"):

    import time
    import os
    import nibabel as nib
    import numpy as np

    from nipype.utils.filemanip import split_filename as split_f
    from aonlm import aonlm

    assert len(params) == 3, "Error, params should have 3 values".format(params)
    assert os.path.exists(img_file), "Error, file {} do not exist".format(img_file)

    path, fname , ext = split_f(img_file)

    nib_image=nib.load(img_file)
    image=nib_image.get_data().astype(np.double)

    ## aonlm_denoised
    start_time = time.time()

    if method == "aonlm":
        denoised=aonlm(image, params[0], params[1], params[2])
        denoised_img_file = os.path.abspath(fname + "_aonlm_denoised" + ext)

    elif method == "mabonlm3d":
        denoised=mabonlm3d(image, params[0], params[1], params[2])
        denoised_img_file = os.path.abspath(fname + "_mabonlm3d_denoised" + ext)
    else:
        print("Error, method {} do not exists, breaking".format(method))
        exit(-1)

    end_time = time.time()
    print ("time:",end_time - start_time)

    ## saving denoised file
    nib.save(nib.Nifti1Image(np.asarray(denoised), header = nib_image.get_header(),affine = nib_image.get_affine()), denoised_img_file)

    return denoised_img_file
