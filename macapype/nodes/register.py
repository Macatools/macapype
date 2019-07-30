
def interative_flirt(anat_file, anat_file_BET, template_file, template_mask_file, n_iter):

    import os
    import nipype.interfaces.fsl as fsl

    from nipype.utils.filemanip import split_filename as split_f

    path_t, fname_t, ext_t = split_f(template_file)
    out_file = os.path.abspath(fname_t + "_brain_flirt.nii")
    template_to_anat_file = os.path.abspath(fname_t + "_to_anat.xfm")


    path_a, fname_a, ext_a = split_f(anat_file)

    anat_file_brain_mask = os.path.abspath(fname_a + "_brain_mask.nii.gz")
    anat_file_brain = os.path.abspath(fname_a + "_brain.nii.gz")

    flirt_ref_file = anat_file_BET

    for i in range(n_iter):

        print('Iter flirt {}'.format(i))

        ### first FLIRT: template brain to anat bet
        flirt = fsl.FLIRT()
        flirt.inputs.in_file = template_file
        flirt.inputs.reference = flirt_ref_file

        flirt.inputs.out_matrix_file = template_to_anat_file
        #flirt.inputs.out_file = out_file
        flirt.inputs.cost = "normcorr"

        flirt.run()


        if i < n_iter-1:

            print('Iter apply_flirt {}'.format(i))
            apply_flirt = fsl.ApplyXFM()
            apply_flirt.inputs.in_file = template_mask_file
            apply_flirt.inputs.reference = anat_file_BET
            apply_flirt.inputs.in_matrix_file = template_to_anat_file
            apply_flirt.inputs.apply_xfm = True
            apply_flirt.inputs.interp = "nearestneighbour"
            apply_flirt.inputs.out_file = anat_file_brain_mask
            apply_flirt.run()



            print('Iter apply_mask {}'.format(i))
            #apply_mask = fsl.ApplyMask()
            apply_mask = fsl.BinaryMaths()
            apply_mask.inputs.in_file = anat_file
            apply_mask.inputs.operation = 'mul'
            apply_mask.inputs.operand_file = anat_file_brain_mask
            apply_mask.inputs.out_file = anat_file_brain
            apply_mask.run()

        flirt_ref_file = anat_file_brain

    return anat_file_brain, template_to_anat_file
