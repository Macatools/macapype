#### on the fly function for checking what is passed in "connect"
#### should end up in ~ nipype.utils.misc

#### equivalent of flirt_average in FSL
def average_align(list_img):

    import os
    import nibabel as nib
    import numpy as np

    from nipype.utils.filemanip import split_filename as split_f
    import nipype.interfaces.fsl as fsl
    print list_img

    if isinstance(list_img, list):

        assert len(list_img) > 0,"Error, list should have at least one file"

        if len(list_img) == 1:
            assert os.path.exists(list_img[0])
            av_img_file = list_img[0]
        else:

            img_0 = nib.load(list_img[0])
            path, fname, ext  = split_f(list_img[0])

            list_data = [img_0.get_data()]
            for i,img in enumerate(list_img[1:]):

                print("running flirt on {}".format(img))
                flirt  =  fsl.FLIRT(dof = 6)
                #flirt.inputs.output_type = "NIFTI_GZ"
                flirt.inputs.in_file = img
                flirt.inputs.reference = list_img[0]
                flirt.inputs.interp = "sinc"
                flirt.inputs.no_search = True
                #flirt.inputs.out_file = os.path.abspath("tmp_" + str(i) + ext)
                out_file = flirt.run().outputs.out_file
                print (out_file)

                data = nib.load(out_file).get_data()
                list_data.append(data)

                #os.remove(out_file)

            avg_data = np.mean(np.array(list_data), axis = 0)
            print (avg_data.shape)

            av_img_file = os.path.abspath("avg_" + fname + ext)
            nib.save(nib.Nifti1Image(avg_data, header = img_0.get_header(), affine = img_0.get_affine()),av_img_file)

    else:
        assert os.path.exists(list_img)
        av_img_file = list_img

    return av_img_file


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


def wrap_antsAtroposN4(dimension, shft_aff_file, brainmask_file, numberOfClasses, ex_prior):

    import os
    import shutil
    from nipype.utils.filemanip import split_filename as split_f
    _, prior_fname, prior_ext = split_f(ex_prior[-1]) ## last element

    ### copying file locally
    dest = os.path.abspath("")

    for prior_file in ex_prior[2:]:
        print (prior_file)
        shutil.copy(prior_file,dest)

    shutil.copy(shft_aff_file,dest)
    shutil.copy(brainmask_file,dest)

    _, bmask_fname, bmask_ext = split_f(brainmask_file)
    _, shft_aff_fname, shft_aff_ext = split_f(shft_aff_file)

    ### generating template_file
    #TODO should be used by default
    template_file = "tmp_%02d.nii.gz"

    ### generating bash_line
    os.chdir(dest)

    out_pref = "segment_"
    bash_line = "bash antsAtroposN4.sh -d {} -a {} -x {} -c {} -p {} -o {}".format(
        dimension,shft_aff_fname+ shft_aff_ext ,bmask_fname+bmask_ext,numberOfClasses,template_file,out_pref)
    print("bash_line : "+bash_line)

    os.system(bash_line)

    #out_files = [os.path.abspath(out_pref+"Segmentation"+fname+prior_ext) for fname in ["","Posteriors01","Posteriors02","Posteriors03"]]

    seg_file = os.path.abspath(out_pref+"Segmentation"+prior_ext)
    seg_post1_file = os.path.abspath(out_pref+"SegmentationPosteriors01"+prior_ext)
    seg_post2_file = os.path.abspath(out_pref+"SegmentationPosteriors02"+prior_ext)
    seg_post3_file = os.path.abspath(out_pref+"SegmentationPosteriors03"+prior_ext)

    out_files = [seg_file,seg_post1_file,seg_post2_file,seg_post3_file]

    #TODO surely more robust way can be used
    return out_files, seg_file, seg_post1_file, seg_post2_file, seg_post3_file

########### NMT_subject_align

def wrap_NMT_subject_align(T1_file):

    import os
    import shutil
    from nipype.utils.filemanip import split_filename as split_f

    nmt_dir="/hpc/meca/users/loh.k/macaque_preprocessing/NMT_v1.2/"
    nmt_ss_file = os.path.join(nmt_dir,"NMT_SS.nii.gz")
    #shutil.copy(nmt_ss_file,cur_dir)

    script_file = os.path.join(nmt_dir,"NMT_subject_align.csh")

    path, fname, ext = split_f(nmt_ss_file)
    #shutil.copy(T1_file,cur_dir)

    ## just to be sure...
    #os.chdir(nmt_dir)

    os.system("tcsh -x {} {} {}".format(script_file, nmt_ss_file, T1_file))

    shft_aff_file = os.path.abspath(fname + "_shft_aff" + ext )
    warpinv_file = os.path.abspath(fname + "_shft_WARPINV" + ext )

    transfo_file = os.path.abspath(fname + "_composite_linear_to_NMT.1D")
    inv_transfo_file = os.path.abspath(fname + "_composite_linear_to_NMT_inv.1D")


    return shft_aff_file, warpinv_file, transfo_file, inv_transfo_file

########### add Nwarp
def add_Nwarp(list_prior_files):

    out_files = []
    for prior_file in list_prior_files[:3]:

        path, fname, ext = split_f(prior_file)
        #out_files.append(os.path.join(path,fname + "_Nwarp" + ext))
        out_files.append(fname + "_Nwarp" + ext)

    for i in range(1,4):
        out_files.append("tmp_%02d.nii.gz"%i)

    return out_files
