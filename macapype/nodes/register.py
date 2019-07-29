
def interative_flirt(anat_file, template_file, template_mask_file, n_iter):

    import os
    import nipype.interface.fsl as fsl

    from nipype.utils.filemanip import split_filename as split_f

    path, fname, ext = split_f(template_file)
    out_file = os.path.abspath(fname + "_brain_flirt.nii")
    out_matrix_file = os.path.abspath(fname + "_to_anat.xfm")


    path, fname, ext = split_f(anat_file)
    anat_mask_file = os.path.abspath(fname + "brain_mask" + ext)



    for i in range(n_iter):

        flirt = fsl.Flirt()
        flirt.inputs.in_file = template_file
        flirt.inputs.reference = anat_file

        flirt.inputs.out_matrix_file = out_matrix_file
        flirt.inputs.out_file = out_file
        flirt.inputs.cost = "normcorr"

        flirt.run()


        if i < n_iter-1:

            apply_flirt = fsl.ApplyXFM()
            apply_flirt.inputs.infile = template_mask_file
            apply_flirt.inputs.reference = anat_file
            apply_flirt.inputs.in_matrix_file = out_matrix_file
            apply_flirt.inputs.apply_xfm = True
            apply_flirt.inputs.interp = "nearestneighbour"
            apply_flirt.run()

    return brain_file
