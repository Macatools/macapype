

def wrap_antsAtroposN4(dimension, shft_aff_file, brainmask_file,
                       numberOfClasses, ex_prior):

    import os
    import shutil
    from nipype.utils.filemanip import split_filename as split_f

    _, prior_fname, prior_ext = split_f(ex_prior[-1])  # last element

    # copying file locally
    dest = os.path.abspath("")

    for prior_file in ex_prior[2:]:
        print(prior_file)
        shutil.copy(prior_file, dest)

    shutil.copy(shft_aff_file, dest)
    shutil.copy(brainmask_file, dest)

    _, bmask_fname, bmask_ext = split_f(brainmask_file)
    _, shft_aff_fname, shft_aff_ext = split_f(shft_aff_file)

    # generating template_file
    # TODO should be used by default
    template_file = "tmp_%02d.nii.gz"

    # generating bash_line
    os.chdir(dest)

    out_pref = "segment_"
    bash_line = "bash antsAtroposN4.sh -d {} -a {} -x {} -c {} -p {} -o {\
    }".format(
        dimension, shft_aff_fname+shft_aff_ext, bmask_fname+bmask_ext,
        numberOfClasses, template_file, out_pref)
    print("bash_line : "+bash_line)

    os.system(bash_line)

    seg_file = os.path.abspath(out_pref+"Segmentation"+prior_ext)
    seg_post1_file = os.path.abspath(
        out_pref+"SegmentationPosteriors01"+prior_ext)
    seg_post2_file = os.path.abspath(
        out_pref+"SegmentationPosteriors02"+prior_ext)
    seg_post3_file = os.path.abspath(
        out_pref+"SegmentationPosteriors03"+prior_ext)

    out_files = [seg_file, seg_post1_file, seg_post2_file, seg_post3_file]

    # TODO surely more robust way can be used
    return out_files, seg_file, seg_post1_file, seg_post2_file, seg_post3_file


def wrap_antsAtroposN4_dirty(dimension, brain_file, brainmask_file,
                             numberOfClasses, ex_prior1, ex_prior2, ex_prior3):

    import os
    import shutil
    from nipype.utils.filemanip import split_filename as split_f

    _, prior_fname, prior_ext = split_f(ex_prior1)  # last element

    # copying file locally
    dest = os.path.abspath("")

    shutil.copy(ex_prior1, dest)
    shutil.copy(ex_prior2, dest)
    shutil.copy(ex_prior3, dest)

    shutil.copy(brain_file, dest)
    shutil.copy(brainmask_file, dest)

    _, bmask_fname, bmask_ext = split_f(brainmask_file)
    _, brain_fname, brain_ext = split_f(brain_file)

    # generating template_file
    # TODO should be used by default
    template_file = "tmp_%02d_allineate.nii.gz"

    # generating bash_line
    os.chdir(dest)

    out_pref = "segment_"
    bash_line = "bash antsAtroposN4.sh -d {} -a {} -x {} -c {} -p {} -o {\
    }".format(
        dimension, brain_fname+brain_ext, bmask_fname+bmask_ext,
        numberOfClasses, template_file, out_pref)
    print("bash_line : "+bash_line)

    os.system(bash_line)

    seg_file = os.path.abspath(out_pref+"Segmentation"+prior_ext)
    seg_post1_file = os.path.abspath(
        out_pref+"SegmentationPosteriors01"+prior_ext)
    seg_post2_file = os.path.abspath(
        out_pref+"SegmentationPosteriors02"+prior_ext)
    seg_post3_file = os.path.abspath(
        out_pref+"SegmentationPosteriors03"+prior_ext)

    out_files = [seg_file, seg_post1_file, seg_post2_file, seg_post3_file]

    # TODO surely more robust way can be used
    return out_files, seg_file, seg_post1_file, seg_post2_file, seg_post3_file
