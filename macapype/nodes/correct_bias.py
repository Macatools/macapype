
def interative_N4_debias(input_image, stop_param):

    import os
    from nipype.utils.filemanip import split_filename as split_f

    path, name, ext = split_f(input_image)

    debiased_image = os.path.abspath(name + "_corrected" + ext)

    cmd_line = "N4BiasFieldCorrection -i {} -o {}".format(input_image,
                                                          debiased_image)
    os.system(cmd_line)

    return debiased_image
