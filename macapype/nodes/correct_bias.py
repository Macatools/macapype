
#TODO correct_bias node
def correct_bias_T1_T2(preproc_T1_file, preproc_T2_file, sigma = 8):
    import os

    import nibabel as nib
    import numpy as np

    from scipy.ndimage.filters import gaussian_filter, median_filter
    from scipy.ndimage.morphology import binary_erosion, binary_dilation, grey_dilation

    preproc_T1_img = nib.load(preproc_T1_file)
    preproc_T1 = preproc_T1_img.get_data().astype(float)

    preproc_T2_img = nib.load(preproc_T2_file)
    preproc_T2 = preproc_T2_img.get_data().astype(float)

    print ("non zeros preproc_T1:",np.sum(preproc_T1 != 0.0))
    print ("non zeros preproc_T2:",np.sum(preproc_T2 != 0.0))

    # mult_T1_T2
    mult_T1_T2 = np.sqrt(np.abs(preproc_T1 * preproc_T2))

    print ("non zeros mult_T1_T2:",np.sum(mult_T1_T2 != 0.0))

    ### saving mult_T1_T2 file #TMP
    mult_T1_T2_file = os.path.abspath("mult_T1_T2.nii")
    nib.save(nib.Nifti1Image(mult_T1_T2,header = preproc_T1_img.get_header(),affine = preproc_T1_img.get_affine()),mult_T1_T2_file)

    # meanbrainval
    meanbrainval = np.nanmean(mult_T1_T2[mult_T1_T2 != 0.0])
    print ("meanbrainval: ",meanbrainval)

    #norm_mult
    norm_mult = mult_T1_T2 / meanbrainval
    #print ("norm_mult:", norm_mult)

    print ("non zeros norm_mult:",np.sum(norm_mult != 0.0))


    ### saving norm_mult file
    norm_mult_file = os.path.abspath("norm_mult.nii")
    nib.save(nib.Nifti1Image(norm_mult,header = preproc_T1_img.get_header(),affine = preproc_T1_img.get_affine()),norm_mult_file)

    ### smooth
    # -bin option first
    bin_norm_mult = np.copy(norm_mult)
    bin_norm_mult[bin_norm_mult != 0.0] = 1.0

    print ("non zeros bin_norm_mult:",np.sum(bin_norm_mult != 0.0))

    #### saving bin_norm_mult file #TMP
    #bin_norm_mult_file = os.path.abspath("bin_norm_mult.nii")
    #nib.save(nib.Nifti1Image(bin_norm_mult,header = preproc_T1_img.get_header(),affine = preproc_T1_img.get_affine()),bin_norm_mult_file)

    smooth= gaussian_filter(bin_norm_mult, sigma = sigma)
    print ("non zeros smooth:",np.sum(smooth != 0.0))

    ### saving smooth file #TMP
    smooth_file = os.path.abspath("smooth.nii")
    nib.save(nib.Nifti1Image(smooth,header = preproc_T1_img.get_header(),affine = preproc_T1_img.get_affine()),smooth_file)

    ### norm smooth
    norm_smooth = gaussian_filter(norm_mult.astype(float), sigma = sigma)/smooth.astype(float)
    print ("non zeros norm_smooth:",np.sum(norm_smooth != 0.0))

    ### saving norm_smooth file #TMP
    norm_smooth_file = os.path.abspath("norm_smooth.nii")
    nib.save(nib.Nifti1Image(norm_smooth,header = preproc_T1_img.get_header(),affine = preproc_T1_img.get_affine()),norm_smooth_file)

    ### modulate:
    modulate = norm_mult.astype(float) / norm_smooth.astype(float)
    print ("non zeros modulate:",np.sum(modulate != 0.0))

    ### saving modulate file #TMP
    modulate_file = os.path.abspath("modulate.nii")
    nib.save(nib.Nifti1Image(modulate,header = preproc_T1_img.get_header(),affine = preproc_T1_img.get_affine()),modulate_file)


    ### std_modulate
    std_modulate = np.nanstd(modulate[modulate != 0.0])
    print ("std_modulate: ",std_modulate)


    ### mean_modulate
    mean_modulate = np.nanmean(modulate[modulate != 0.0])
    print ("mean_modulate: ",mean_modulate)

    ### lower
    lower = mean_modulate - (0.5*std_modulate)
    print ("lower: ",lower)

    ### thresh_lower
    thresh_lower = np.copy(modulate)
    thresh_lower[thresh_lower < lower] = 0.0
    print ("non zeros thresh_lower:",np.sum(thresh_lower != 0.0))

    ### saving thresh_lower file
    thresh_lower_file = os.path.abspath("thresh_lower.nii")
    nib.save(nib.Nifti1Image(thresh_lower,header = preproc_T1_img.get_header(),affine = preproc_T1_img.get_affine()),thresh_lower_file)

    ### mod_mask
    bin_thresh_lower = np.copy(thresh_lower)
    bin_thresh_lower [bin_thresh_lower != 0.0] = 1.0 # -bin
    print ("non zeros bin_thresh_lower:",np.sum(bin_thresh_lower != 0.0))

    #print ("bin:", thresh_lower)
    mod_mask = binary_erosion(bin_thresh_lower)*255 # -ero -mul 255
    print ("non zeros mod_mask:",np.sum(mod_mask != 0.0))

    ### saving mod_mask file #TMP
    mod_mask_file = os.path.abspath("mod_mask.nii")
    nib.save(nib.Nifti1Image(mod_mask,header = preproc_T1_img.get_header(),affine = preproc_T1_img.get_affine()),mod_mask_file)

    ## bias
    bias = np.zeros(shape = norm_mult.shape)
    bias[mod_mask != 0] = norm_mult [mod_mask != 0]

    print ("non zeros bias:",np.sum(bias != 0.0))
    norm_mult [mod_mask == 0] = 0.0 # -mas mod_mask
    print ("non zeros norm_mult:",np.sum(norm_mult != 0.0))

    #diff = bias - norm_mult
    #print (diff)
    #print (np.max(diff))
    #0/0

    #bias = grey_dilation(norm_mult, size = (3,3,3), structure = np.ones((3,3,3))) # -dilall
    ##bias = binary_dilation(norm_mult) # -dilall
    #print ("non zeros bias:",np.sum(bias != 0.0))

    all_non_zeros = False

    bias = np.copy(norm_mult)

    nb_zeros = np.sum(bias == 0.0)
    print (nb_zeros)

    while all_non_zeros == False:

        bias = binary_dilation(bias, size = (3,3,3), structure = np.ones((3,3,3))) # -dilall

        nb_zeros = np.sum(bias == 0.0)

        print (nb_zeros)
        if nb_zeros == 0:
            all_non_zeros = True


        ### saving bias file
        bias_file = os.path.abspath("bias.nii")
        nib.save(nib.Nifti1Image(bias,header = preproc_T1_img.get_header(),affine = preproc_T1_img.get_affine()),bias_file)

    #bias = binary_dilation(norm_mult) # -dilall
    print ("non zeros bias:",np.sum(bias != 0.0))


    0/0
    ### smooth_bias
    smooth_bias = gaussian_filter(bias.astype(float), sigma = sigma)
    print ("non zeros smooth_bias:",np.sum(smooth_bias != 0.0))

    ### saving smooth_bias file
    smooth_bias_file = os.path.abspath("smooth_bias.nii")
    nib.save(nib.Nifti1Image(smooth_bias,header = preproc_T1_img.get_header(),affine = preproc_T1_img.get_affine()),smooth_bias_file)

    ### restore_T1
    restore_T1 = preproc_T1/smooth_bias
    print ("non zeros restore_T1:",np.sum(smooth_bias != 0.0))

    ### saving restore_T1 file
    restore_T1_file = os.path.abspath("restore_T1.nii")
    nib.save(nib.Nifti1Image(restore_T1,header = preproc_T1_img.get_header(),affine = preproc_T1_img.get_affine()),restore_T1_file)


    ### restore_T2
    restore_T2 = preproc_T2/smooth_bias
    print ("non zeros restore_T2:",np.sum(smooth_bias != 0.0))


    ### saving restore_T2 file
    restore_T2_file = os.path.abspath("restore_T2.nii")
    nib.save(nib.Nifti1Image(restore_T2,header = preproc_T2_img.get_header(),affine = preproc_T2_img.get_affine()),restore_T2_file)

    return thresh_lower_file, norm_mult_file, bias_file, smooth_bias_file, restore_T1_file, restore_T2_file


def interative_N4_debias(input_image, stop_param):

    import os
    from nipype.utils.filemanip import split_filename as split_f

    path,name,ext = split_f(input_image)

    debiased_image = os.path.abspath( name + "_corrected" + ext)

    cmd_line = "N4BiasFieldCorrection -i {} -o {}".format(input_image,
                                                          debiased_image)
    os.system(cmd_line)

    return debiased_image



