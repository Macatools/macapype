import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl

from ..utils.utils_nodes import NodeParams, parse_key


def create_correct_bias_pipe(params={}, name="correct_bias_pipe"):
    """
    Description: Correct bias using T1 and T2 images
        Same as bash_regis.T1xT2BiasFieldCorrection

    Params:

        - smooth (see `MathsCommand <https://nipype.readthedocs.io/en/0.12.1/\
        interfaces/generated/nipype.interfaces.fsl.maths.html#mathscommand>`_)
        - norm_smooth (see `MultiMathsCommand <https://nipype.readthedocs.io/\
        en/0.12.1/interfaces/generated/nipype.interfaces.fsl.maths.html\
        #multiimagemaths>`_)
        - smooth_bias (see `IsotropicSmooth <https://nipype.readthedocs.io/en/\
        0.12.1/interfaces/generated/nipype.interfaces.fsl.maths.html#\
        isotropicsmooth>`_)

    Inputs:

        inputnode:

            preproc_T1:
                preprocessed T1 file name

            preproc_T2:
                preprocessed T2 file name

        arguments:

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "correct_bias_pipe")

    Outputs:

        outputnode.debiased_T1:
            T1 after bias correction

        outputnode.debiased_T2:
            T2 after bias correction
    """
    # creating pipeline
    correct_bias_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['preproc_T1', 'preproc_T2']),
        name='inputnode')

    # BinaryMaths
    mult_T1_T2 = pe.Node(fsl.BinaryMaths(), name='mult_T1_T2')
    mult_T1_T2.inputs.operation = "mul"
    mult_T1_T2.inputs.args = "-abs -sqrt"
    mult_T1_T2.inputs.output_datatype = "float"

    correct_bias_pipe.connect(inputnode, 'preproc_T1', mult_T1_T2, 'in_file')
    correct_bias_pipe.connect(inputnode, 'preproc_T2',
                              mult_T1_T2, 'operand_file')

    # Mean Brain Val
    meanbrainval = pe.Node(fsl.ImageStats(), name='meanbrainval')
    meanbrainval.inputs.op_string = "-M"

    correct_bias_pipe.connect(mult_T1_T2, 'out_file', meanbrainval, 'in_file')

    # norm_mult
    norm_mult = pe.Node(fsl.BinaryMaths(), name='norm_mult')
    norm_mult.inputs.operation = "div"

    correct_bias_pipe.connect(mult_T1_T2, 'out_file', norm_mult, 'in_file')
    correct_bias_pipe.connect(meanbrainval, 'out_stat',
                              norm_mult, 'operand_value')

    # smooth
    smooth = NodeParams(fsl.maths.MathsCommand(),
                        params=parse_key(params, "smooth"),
                        name='smooth')

    correct_bias_pipe.connect(norm_mult, 'out_file', smooth, 'in_file')

    # norm_smooth
    norm_smooth = NodeParams(fsl.MultiImageMaths(),
                             params=parse_key(params, "norm_smooth"),
                             name='norm_smooth')

    correct_bias_pipe.connect(norm_mult, 'out_file', norm_smooth, 'in_file')
    correct_bias_pipe.connect(smooth, 'out_file', norm_smooth, 'operand_files')

    # modulate
    modulate = pe.Node(fsl.BinaryMaths(), name='modulate')
    modulate.inputs.operation = "div"

    correct_bias_pipe.connect(norm_mult, 'out_file',
                              modulate, 'in_file')
    correct_bias_pipe.connect(norm_smooth, 'out_file',
                              modulate, 'operand_file')

    # std_modulate
    std_modulate = pe.Node(fsl.ImageStats(), name='std_modulate')
    std_modulate.inputs.op_string = "-S"

    correct_bias_pipe.connect(modulate, 'out_file', std_modulate, 'in_file')

    # mean_modulate
    mean_modulate = pe.Node(fsl.ImageStats(), name='mean_modulate')
    mean_modulate.inputs.op_string = "-M"

    correct_bias_pipe.connect(modulate, 'out_file', mean_modulate, 'in_file')

    # compute_lower_val
    def compute_lower_val(mean_val, std_val):
        return mean_val - (std_val*0.5)

    # compute_lower
    lower = pe.Node(niu.Function(input_names=['mean_val', 'std_val'],
                                 output_names=['lower_val'],
                                 function=compute_lower_val),
                    name='lower')

    correct_bias_pipe.connect(mean_modulate, 'out_stat', lower, 'mean_val')
    correct_bias_pipe.connect(std_modulate, 'out_stat', lower, 'std_val')

    # thresh_lower
    thresh_lower = pe.Node(fsl.Threshold(), name='thresh_lower')

    correct_bias_pipe.connect(lower, 'lower_val', thresh_lower, 'thresh')
    correct_bias_pipe.connect(modulate, 'out_file', thresh_lower, 'in_file')

    # mod_mask
    mod_mask = pe.Node(fsl.UnaryMaths(), name='mod_mask')
    mod_mask.inputs.operation = "bin"
    mod_mask.inputs.args = "-ero -mul 255"

    correct_bias_pipe.connect(thresh_lower, 'out_file', mod_mask, 'in_file')

    # bias
    bias = pe.Node(fsl.MultiImageMaths(), name='bias')
    bias.inputs.op_string = "-mas %s -dilall"
    bias.inputs.output_datatype = "float"

    correct_bias_pipe.connect(norm_mult, 'out_file', bias, 'in_file')

    correct_bias_pipe.connect(mod_mask, 'out_file', bias, 'operand_files')

    # smooth_bias
    smooth_bias = NodeParams(fsl.IsotropicSmooth(),
                             params=parse_key(params, "smooth_bias"),
                             name='smooth_bias')

    correct_bias_pipe.connect(bias, 'out_file', smooth_bias, 'in_file')

    # debiased_T1
    debiased_T1 = pe.Node(fsl.BinaryMaths(), name='debiased_T1')
    debiased_T1.inputs.operation = "div"
    debiased_T1.inputs.output_datatype = "float"

    correct_bias_pipe.connect(inputnode, 'preproc_T1',
                              debiased_T1, 'in_file')
    correct_bias_pipe.connect(smooth_bias, 'out_file',
                              debiased_T1, 'operand_file')

    # debiased_T2
    debiased_T2 = pe.Node(fsl.BinaryMaths(), name='debiased_T2')
    debiased_T2.inputs.operation = "div"
    debiased_T2.inputs.output_datatype = "float"

    correct_bias_pipe.connect(inputnode, 'preproc_T2',
                              debiased_T2, 'in_file')
    correct_bias_pipe.connect(smooth_bias, 'out_file',
                              debiased_T2, 'operand_file')

    # outputnode
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["debiased_T1", "debiased_T2"]),
        name='outputnode')

    correct_bias_pipe.connect(debiased_T1, 'out_file',
                              outputnode, 'debiased_T1')
    correct_bias_pipe.connect(debiased_T2, 'out_file',
                              outputnode, 'debiased_T2')

    return correct_bias_pipe


def create_masked_correct_bias_pipe(params={},
                                    name="masked_correct_bias_pipe"):
    """
    Description: Correct bias using T1 and T2 images in a mask
        Same as bash_regis.T1xT2BiasFieldCorrection

    Params:

        - smooth (see `MathsCommand <https://nipype.readthedocs.io/en/0.12.1/\
        interfaces/generated/nipype.interfaces.fsl.maths.html#mathscommand>`_)
        - norm_smooth (see `MultiMathsCommand <https://nipype.readthedocs.io/\
        en/0.12.1/interfaces/generated/nipype.interfaces.fsl.maths.html\
        #multiimagemaths>`_)
        - smooth_bias (see `IsotropicSmooth <https://nipype.readthedocs.io/en/\
        0.12.1/interfaces/generated/nipype.interfaces.fsl.maths.html#\
        isotropicsmooth>`_)

    Inputs:

        inputnode:

            preproc_T1:
                preprocessed T1 file name

            preproc_T2:
                preprocessed T2 file name

            brain_mask:
                brain mask where operation will be applied

        arguments:

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "masked_correct_bias_pipe")

    Outputs:

        outputnode.debiased_T1:
            T1 after bias correction

        outputnode.debiased_T2:
            T2 after bias correction

        outputnode.mask_debiased_T1:
            Masked T1 after bias correction

        outputnode.mask_debiased_T2:
            Masked T2 after bias correction

    """

    # creating pipeline
    masked_correct_bias_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['preproc_T1', 'preproc_T2',
                                      'brain_mask']),
        name='inputnode')

    # BinaryMaths
    mult_T1_T2 = pe.Node(fsl.BinaryMaths(), name='mult_T1_T2')
    mult_T1_T2.inputs.operation = "mul"
    mult_T1_T2.inputs.args = "-abs -sqrt"
    mult_T1_T2.inputs.output_datatype = "float"

    masked_correct_bias_pipe.connect(inputnode, 'preproc_T1',
                                     mult_T1_T2, 'in_file')
    masked_correct_bias_pipe.connect(inputnode, 'preproc_T2',
                                     mult_T1_T2, 'operand_file')

    # mask mult
    mask_mult = pe.Node(fsl.ApplyMask(), name='mask_mult')

    masked_correct_bias_pipe.connect(mult_T1_T2, 'out_file',
                                     mask_mult, 'in_file')
    masked_correct_bias_pipe.connect(inputnode, 'brain_mask',
                                     mask_mult, 'mask_file')

    # Mean Brain Val
    meanbrainval = pe.Node(fsl.ImageStats(), name='meanbrainval')
    meanbrainval.inputs.op_string = "-M"

    masked_correct_bias_pipe.connect(mult_T1_T2, 'out_file',
                                     meanbrainval, 'in_file')

    # norm_mult
    norm_mult = pe.Node(fsl.BinaryMaths(), name='norm_mult')
    norm_mult.inputs.operation = "div"

    masked_correct_bias_pipe.connect(mask_mult, 'out_file',
                                     norm_mult, 'in_file')
    masked_correct_bias_pipe.connect(meanbrainval, 'out_stat',
                                     norm_mult, 'operand_value')

    # smooth
    smooth = NodeParams(fsl.maths.MathsCommand(),
                        params=parse_key(params, "smooth"),
                        name='smooth')

    masked_correct_bias_pipe.connect(norm_mult, 'out_file', smooth, 'in_file')

    # norm_smooth
    norm_smooth = NodeParams(fsl.MultiImageMaths(),
                             params=parse_key(params, "norm_smooth"),
                             name='norm_smooth')

    masked_correct_bias_pipe.connect(norm_mult, 'out_file',
                                     norm_smooth, 'in_file')
    masked_correct_bias_pipe.connect(smooth, 'out_file',
                                     norm_smooth, 'operand_files')

    # modulate
    modulate = pe.Node(fsl.BinaryMaths(), name='modulate')
    modulate.inputs.operation = "div"

    masked_correct_bias_pipe.connect(norm_mult, 'out_file',
                                     modulate, 'in_file')

    masked_correct_bias_pipe.connect(norm_smooth, 'out_file',
                                     modulate, 'operand_file')

    # std_modulate
    std_modulate = pe.Node(fsl.ImageStats(), name='std_modulate')
    std_modulate.inputs.op_string = "-S"

    masked_correct_bias_pipe.connect(modulate, 'out_file',
                                     std_modulate, 'in_file')

    # mean_modulate
    mean_modulate = pe.Node(fsl.ImageStats(), name='mean_modulate')
    mean_modulate.inputs.op_string = "-M"

    masked_correct_bias_pipe.connect(modulate, 'out_file',
                                     mean_modulate, 'in_file')

    # function lower val
    def compute_lower_val(mean_val, std_val):
        return mean_val - (std_val*0.5)

    # compute_lower
    lower = pe.Node(niu.Function(input_names=['mean_val', 'std_val'],
                                 output_names=['lower_val'],
                                 function=compute_lower_val),
                    name='lower')

    masked_correct_bias_pipe.connect(mean_modulate, 'out_stat',
                                     lower, 'mean_val')
    masked_correct_bias_pipe.connect(std_modulate, 'out_stat',
                                     lower, 'std_val')

    # thresh_lower
    thresh_lower = pe.Node(fsl.Threshold(), name='thresh_lower')

    masked_correct_bias_pipe.connect(lower, 'lower_val',
                                     thresh_lower, 'thresh')
    masked_correct_bias_pipe.connect(modulate, 'out_file',
                                     thresh_lower, 'in_file')

    # mod_mask
    mod_mask = pe.Node(fsl.UnaryMaths(), name='mod_mask')
    mod_mask.inputs.operation = "bin"
    mod_mask.inputs.args = "-ero -mul 255"

    masked_correct_bias_pipe.connect(thresh_lower, 'out_file',
                                     mod_mask, 'in_file')

    """
    ##tmp_bias
    tmp_bias = pe.Node(fsl.MultiImageMaths(),name='tmp_bias')
    tmp_bias.inputs.op_string = "-mas %s"
    tmp_bias.inputs.output_datatype = "float"

    masked_correct_bias_pipe.connect(norm_mult, 'out_file',
                                     tmp_bias, 'in_file')

    masked_correct_bias_pipe.connect(mod_mask, 'out_file',
                                     tmp_bias, 'operand_files')
    """
    # bias
    bias = pe.Node(fsl.MultiImageMaths(), name='bias')
    bias.inputs.op_string = "-mas %s -dilall"
    bias.inputs.output_datatype = "float"

    masked_correct_bias_pipe.connect(norm_mult, 'out_file',
                                     bias, 'in_file')

    masked_correct_bias_pipe.connect(mod_mask, 'out_file',
                                     bias, 'operand_files')

    # smooth_bias
    smooth_bias = NodeParams(fsl.IsotropicSmooth(),
                             params=parse_key(params, "smooth_bias"),
                             name='smooth_bias')

    masked_correct_bias_pipe.connect(bias, 'out_file',
                                     smooth_bias, 'in_file')

    # debiased_T1
    debiased_T1 = pe.Node(fsl.BinaryMaths(), name='debiased_T1')
    debiased_T1.inputs.operation = "div"
    debiased_T1.inputs.output_datatype = "float"

    masked_correct_bias_pipe.connect(inputnode, 'preproc_T1',
                                     debiased_T1, 'in_file')
    masked_correct_bias_pipe.connect(smooth_bias, 'out_file',
                                     debiased_T1, 'operand_file')

    # debiased_T2
    debiased_T2 = pe.Node(fsl.BinaryMaths(), name='debiased_T2')
    debiased_T2.inputs.operation = "div"
    debiased_T2.inputs.output_datatype = "float"

    masked_correct_bias_pipe.connect(inputnode, 'preproc_T2',
                                     debiased_T2, 'in_file')
    masked_correct_bias_pipe.connect(smooth_bias, 'out_file',
                                     debiased_T2, 'operand_file')

    # mask_debiased_T1
    mask_debiased_T1 = pe.Node(fsl.ApplyMask(), name='mask_debiased_T1')

    masked_correct_bias_pipe.connect(debiased_T1, 'out_file',
                                     mask_debiased_T1, 'in_file')
    masked_correct_bias_pipe.connect(inputnode, 'brain_mask',
                                     mask_debiased_T1, 'mask_file')

    # mask_debiased_T2
    mask_debiased_T2 = pe.Node(fsl.ApplyMask(), name='mask_debiased_T2')

    masked_correct_bias_pipe.connect(debiased_T2, 'out_file',
                                     mask_debiased_T2, 'in_file')
    masked_correct_bias_pipe.connect(inputnode, 'brain_mask',
                                     mask_debiased_T2, 'mask_file')

    # outputnode
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["debiased_T1", "debiased_T2", "mask_debiased_T1",
                    "mask_debiased_T2"]),
        name='outputnode')

    masked_correct_bias_pipe.connect(debiased_T1, 'out_file', outputnode,
                                     'debiased_T1')
    masked_correct_bias_pipe.connect(debiased_T2, 'out_file', outputnode,
                                     'debiased_T2')

    masked_correct_bias_pipe.connect(mask_debiased_T1, 'out_file', outputnode,
                                     'mask_debiased_T1')
    masked_correct_bias_pipe.connect(mask_debiased_T2, 'out_file', outputnode,
                                     'mask_debiased_T2')

    return masked_correct_bias_pipe
