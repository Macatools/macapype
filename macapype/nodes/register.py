
def interative_flirt(anat_file, anat_file_BET, template_brain_file,
                     template_mask_file, n_iter):
    """
    This funcion, from Regis script, aims at interatively building a better
    skull stripped version of the subject's. There is a need for an already
    computed skullstripped version to initiallized the procedure (anat_file_BET)

    The algo works this way:
    1) flirt skullstripped template to skullstripped subject's brain
    2) apply transfo on template's mask to have the mask in subject's space
    3) mask orig anat with compute mask to obtained a new skullstripped
    subject's brain. Use this new skullstripped subject's for the next
    iteration.
    """

    import os
    import nipype.interfaces.fsl as fsl

    from nipype.utils.filemanip import split_filename as split_f

    path_t, fname_t, ext_t = split_f(template_brain_file)
    out_file = os.path.abspath(fname_t + "_brain_flirt.nii")
    template_to_anat_file = os.path.abspath(fname_t + "_to_anat.xfm")

    path_a, fname_a, ext_a = split_f(anat_file)

    anat_file_brain_mask = os.path.abspath(fname_a + "_brain_mask.nii.gz")
    anat_file_brain = os.path.abspath(fname_a + "_brain.nii")

    flirt_ref_file = anat_file_BET

    for i in range(n_iter):

        print('Iter flirt {}'.format(i))

        # first step = FLIRT: template brain to anat bet
        # -> transfo matrix (linear) between the two
        flirt = fsl.FLIRT()
        flirt.inputs.in_file = template_brain_file
        flirt.inputs.reference = flirt_ref_file

        flirt.inputs.out_matrix_file = template_to_anat_file
        #flirt.inputs.out_file = out_file
        flirt.inputs.cost = "normcorr"

        flirt.run()

        # second step = apply transfo to template's mask
        # -> brain_mask in subject's space
        print('Iter apply_flirt {}'.format(i))
        apply_flirt = fsl.ApplyXFM()
        apply_flirt.inputs.in_file = template_mask_file
        apply_flirt.inputs.reference = anat_file_BET
        apply_flirt.inputs.in_matrix_file = template_to_anat_file
        apply_flirt.inputs.apply_xfm = True
        apply_flirt.inputs.interp = "nearestneighbour"
        apply_flirt.inputs.out_file = anat_file_brain_mask
        apply_flirt.run()


        # third step = use the mask in subject's space to mask the build
        # a skull-stripped version of the subject's brain
        # -> better skullstripped version
        print('Iter apply_mask {}'.format(i))
        #apply_mask = fsl.ApplyMask() ### a voir si plus pertinent...
        apply_mask = fsl.BinaryMaths()
        apply_mask.inputs.in_file = anat_file
        apply_mask.inputs.operation = 'mul'
        apply_mask.inputs.operand_file = anat_file_brain_mask
        apply_mask.inputs.out_file = anat_file_brain
        apply_mask.inputs.output_type = "NIFTI"
        apply_mask.run()

        flirt_ref_file = anat_file_brain

    return anat_file_brain, template_to_anat_file


########### NMT_subject_align
def wrap_NMT_subject_align(T1_file):

    import os
    import shutil

    from nipype.utils.filemanip import split_filename as split_f

    nmt_dir="/hpc/meca/users/loh.k/macaque_preprocessing/NMT_v1.2/"
    nmt_ss_file = os.path.join(nmt_dir,"NMT_SS.nii.gz")
    #shutil.copy(nmt_ss_file,cur_dir)

    script_file = os.path.join(nmt_dir,"NMT_subject_align.csh")

    path, fname, ext = split_f(T1_file)
    #shutil.copy(T1_file,cur_dir)

    ## just to be sure...
    #os.chdir(nmt_dir)

    os.system("tcsh -x {} {} {}".format(script_file, T1_file, nmt_ss_file))

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
        out_files.append(os.path.abspath(fname + "_Nwarp" + ext))

    for i in range(1,4):
        out_files.append(os.path.abspath("tmp_%02d.nii.gz"%i))

    return out_files
