def wrap_antsAtroposN4_dirty(dimension, brain_file, brainmask_file, numberOfClasses, ex_prior1, ex_prior2, ex_prior3):

    import os
    import shutil
    from nipype.utils.filemanip import split_filename as split_f

    _, prior_fname, prior_ext = split_f(ex_prior1) ## last element

    ### copying file locally
    dest = os.path.abspath("")

    shutil.copy(ex_prior1,dest)
    shutil.copy(ex_prior2,dest)
    shutil.copy(ex_prior3,dest)

    shutil.copy(brain_file,dest)
    shutil.copy(brainmask_file,dest)

    _, bmask_fname, bmask_ext = split_f(brainmask_file)
    _, brain_fname, brain_ext = split_f(brain_file)

    ### generating template_file
    #TODO should be used by default
    template_file = "tmp_%02d_allineate.nii.gz"

    ### generating bash_line
    os.chdir(dest)

    out_pref = "segment_"
    bash_line = "bash antsAtroposN4.sh -d {} -a {} -x {} -c {} -p {} -o {}".format(
        dimension,brain_fname+ brain_ext ,bmask_fname+bmask_ext,numberOfClasses,template_file,out_pref)
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

    import os
    from nipype.utils.filemanip import split_filename as split_f

    out_files = []
    for prior_file in list_prior_files[:3]:

        path, fname, ext = split_f(prior_file)
        #out_files.append(os.path.join(path,fname + "_Nwarp" + ext))
        out_files.append(os.path.join(path,fname + "_Nwarp" + ext))

    for i in range(1,4):
        out_files.append(os.path.join(path,"tmp_%02d.nii.gz"%i))

    return out_files
