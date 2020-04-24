
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from macapype.nodes.correct_bias import T1xT2BiasFieldCorrection
from macapype.nodes.register import IterREGBET

from .prepare import create_data_preparation_pipe

from .segment import (create_old_segment_pipe,
                      create_segment_atropos_pipe)

from .correct_bias import (create_masked_correct_bias_pipe,
                           create_correct_bias_pipe)

from .register import create_register_NMT_pipe

from .extract_brain import create_extract_pipe

from macapype.utils.misc import gunzip


###############################################################################
# Regis
def create_brain_register_pipe(params_template, params={},
                               name="brain_register_pipe"):

    # Creating pipeline
    brain_register_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1_cropped', 'T2_cropped', "mask"]),
        name='inputnode'
    )

    # Bias correction of cropped images
    if "debias" in params.keys():
        s = params["debias"]["s"]
    else:
        s = 4

    debias = pe.Node(T1xT2BiasFieldCorrection(s=s), name='debias')

    brain_register_pipe.connect(inputnode, 'T1_cropped', debias, 't1_file')
    brain_register_pipe.connect(inputnode, 'T2_cropped', debias, 't2_file')
    brain_register_pipe.connect(inputnode, 'mask', debias, 'b')

    # Iterative registration to the INIA19 template
    reg = pe.Node(IterREGBET(), name='reg')
    reg.inputs.refb_file = params_template["template_brain"]

    if "reg" in params.keys() and "n" in params["reg"].keys():
        reg.inputs.n = params["reg"]["n"]

    if "reg" in params.keys() and "m" in params["reg"].keys():
        reg.inputs.m = params["reg"]["m"]

    if "reg" in params.keys() and "dof" in params["reg"].keys():
        reg.inputs.dof = params["reg"]["dof"]

    brain_register_pipe.connect(debias, 't1_debiased_file', reg, 'inw_file')
    brain_register_pipe.connect(debias, 't1_debiased_brain_file',
                                reg, 'inb_file')

    return brain_register_pipe


def create_full_T1xT2_segment_pnh_subpipes(
        params_template, params={}, name='full_T1xT2_segment_pnh_subpipes'):
    """ Description: Regis T1xT2 pipeline

        - T1xT2BET brain extraction and crop -> mask
        - T1xT2BiasFieldCorrection using mask -> better mask
        - NMT align (after N4Debias)
        - Atropos segment

    Inputs:

        inputnode:
            T1: T1 file name

            T2: T2 file name

        arguments:
            params_template: dict of template files containing brain_template
            and priors (list of template based segmented tissues)

            params: dictionary of node sub-parameters (from a json file)

            name: pipeline name (default = "T1xT2_segmentation_pipeline")

    Outputs:
            old_segment_pipe.thresh_gm.out_file:
                segmented grey matter in template space

            old_segment_pipe.thresh_wm.out_file:
                segmented white matter in template space

            old_segment_pipe.thresh_csf.out_file:
                segmented csf in template space
    """

    print("Full pipeline name: ", name)

    # Creating pipeline
    seg_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1', 'T2']),
        name='inputnode'
    )

    # average_align, T1xT2BET
    if 'data_preparation_pipe' in params.keys():
        print("data_preparation_pipe is in params")
        params_data_preparation_pipe = params["data_preparation_pipe"]
    else:
        print("*** data_preparation_pipe NOT in params")
        params_data_preparation_pipe = {}

    data_preparation_pipe = create_data_preparation_pipe(
        params_data_preparation_pipe)

    seg_pipe.connect(inputnode, 'T1', data_preparation_pipe, 'inputnode.T1')
    seg_pipe.connect(inputnode, 'T2', data_preparation_pipe, 'inputnode.T2')

    if 'brain_register_pipe' in params.keys():
        print("brain_register_pipe is in params")
        params_brain_register_pipe = params["brain_register_pipe"]
    else:
        print("*** brain_register_pipe NOT in params")
        params_brain_register_pipe = {}

    brain_register_pipe = create_brain_register_pipe(
        params_template,
        params=params_brain_register_pipe)

    seg_pipe.connect(data_preparation_pipe, 'bet_crop.t1_cropped_file',
                     brain_register_pipe, 'inputnode.T1_cropped')
    seg_pipe.connect(data_preparation_pipe, 'bet_crop.t2_cropped_file',
                     brain_register_pipe, 'inputnode.T2_cropped')
    seg_pipe.connect(data_preparation_pipe, 'bet_crop.mask_file',
                     brain_register_pipe, 'inputnode.mask')

    # Compute brain mask using old_segment of SPM and postprocessing on
    # tissues' masks
    if "old_segment_pipe" in params.keys():
        params_old_segment_pipe = params["old_segment_pipe"]
    else:
        params_old_segment_pipe = {}

    old_segment_pipe = create_old_segment_pipe(
        params_template, params=params_old_segment_pipe)

    seg_pipe.connect(brain_register_pipe, ('reg.warp_file', gunzip),
                     old_segment_pipe, 'inputnode.T1')

    return seg_pipe


###############################################################################
# Kepkee

def create_brain_extraction_pipe(params_template, params={},
                                 name="brain_extraction_pipe"):
    """
    Description:


    - correct_bias
    - denoise
    - extract_brain
    Inputs:

        inputnode:
            preproc_T1: preprocessed T1 file name
            preproc_T2: preprocessed T2 file name


        arguments:
            params_template: dictionary of template files
            params: dictionary of node sub-parameters (from a json file)
            name: pipeline name (default = "full_segment_pipe")

    Outputs:

    """
    # creating pipeline
    brain_extraction_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['preproc_T1', 'preproc_T2']),
        name='inputnode'
    )

    # Correct_bias_T1_T2
    if "correct_bias_pipe" in params.keys():
        params_correct_bias_pipe = params["correct_bias_pipe"]
    else:
        params_correct_bias_pipe = {}

    correct_bias_pipe = create_correct_bias_pipe(
        params=params_correct_bias_pipe)

    brain_extraction_pipe.connect(inputnode, 'preproc_T1',
                                  correct_bias_pipe, 'inputnode.preproc_T1')
    brain_extraction_pipe.connect(inputnode, 'preproc_T2',
                                  correct_bias_pipe, 'inputnode.preproc_T2')

    # brain extraction
    if "extract_pipe" in params.keys():  # so far, unused
        params_extract_pipe = params["extract_pipe"]

    else:
        params_extract_pipe = {}

    extract_pipe = create_extract_pipe(
        params_template=params_template,
        params=params_extract_pipe)

    brain_extraction_pipe.connect(correct_bias_pipe, "restore_T1.out_file",
                                  extract_pipe, "inputnode.restore_T1")
    brain_extraction_pipe.connect(correct_bias_pipe, "restore_T2.out_file",
                                  extract_pipe, "inputnode.restore_T2")

    return brain_extraction_pipe


def create_brain_segment_from_mask_pipe(
        params_template, params={}, name="brain_segment_from_mask_pipe"):
    """ Description: Segment T1 (using T2 for bias correction) and a previously
        computed mask with NMT Atlas and atropos segment.

        - denoise pipe
        - debias pipe
        - NMT align (after N4Debias)
        - Atropos segment

    Inputs:

        inputnode:
            preproc_T1: preprocessed T1 file name
            preproc_T2: preprocessed T2 file name
            brain_mask: a mask computed for the same T1/T2 images


        arguments:
            params_template: dictionary of template files

            params: dictionary of node sub-parameters (from a json file)

            name: pipeline name (default = "full_segment_pipe")

    Outputs:

    """
    # creating pipeline
    brain_segment_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['preproc_T1', 'preproc_T2', 'brain_mask']),
        name='inputnode')

    # correcting for bias T1/T2, but this time with a mask
    if "masked_correct_bias_pipe" in params.keys():
        params_masked_correct_bias_pipe = params["masked_correct_bias_pipe"]
    else:
        params_masked_correct_bias_pipe = {}

    masked_correct_bias_pipe = create_masked_correct_bias_pipe(
        params=params_masked_correct_bias_pipe)

    brain_segment_pipe.connect(
        inputnode, 'preproc_T1',
        masked_correct_bias_pipe, "inputnode.preproc_T1")
    brain_segment_pipe.connect(
        inputnode, 'preproc_T2',
        masked_correct_bias_pipe, "inputnode.preproc_T2")

    brain_segment_pipe.connect(
        inputnode, 'brain_mask',
        masked_correct_bias_pipe, "inputnode.brain_mask")

    # register NMT template, template mask and priors to subject T1
    if "register_NMT_pipe" in params.keys():
        params_register_NMT_pipe = params["register_NMT_pipe"]
    else:
        params_register_NMT_pipe = {}

    register_NMT_pipe = create_register_NMT_pipe(
        params_template=params_template, params=params_register_NMT_pipe)

    brain_segment_pipe.connect(
        masked_correct_bias_pipe, 'restore_mask_T1.out_file',
        register_NMT_pipe, "inputnode.T1")

    # ants Atropos
    if "segment_atropos_pipe" in params.keys():
        params_segment_atropos_pipe = params["segment_atropos_pipe"]
    else:
        params_segment_atropos_pipe = {}

    segment_atropos_pipe = create_segment_atropos_pipe(
        params=params_segment_atropos_pipe)

    brain_segment_pipe.connect(
        register_NMT_pipe, 'norm_intensity.output_image',
        segment_atropos_pipe, "inputnode.brain_file")

    brain_segment_pipe.connect(
        register_NMT_pipe, 'align_seg_csf.out_file', segment_atropos_pipe,
        "inputnode.csf_prior_file")
    brain_segment_pipe.connect(register_NMT_pipe, 'align_seg_gm.out_file',
                               segment_atropos_pipe, "inputnode.gm_prior_file")
    brain_segment_pipe.connect(register_NMT_pipe, 'align_seg_wm.out_file',
                               segment_atropos_pipe, "inputnode.wm_prior_file")

    return brain_segment_pipe


# first step for a mask and then call create_full_segment_from_mask_pipe
def create_full_segment_pnh_subpipes(
        params_template, params={}, name="full_segment_pnh_subpipes"):
    """
    Description: Segment T1 (using T2 for bias correction) .

    new version (as it is now)
    - brain preproc (avg and align, reorient of specified cropping from T1xT2BET, bet is optional) # noqa
    - brain extraction (see create_brain_extraction_pipe):
        - correct_bias
        - denoise
        - extract_brain
    - brain segment from mask (see create_brain_segment_from_mask_pipe):
        - denoise pipe
        - debias pipe
        - NMT align (after N4Debias)
        - Atropos segment

    Inputs:

        inputnode:
            preproc_T1: preprocessed T1 file name
            preproc_T2: preprocessed T2 file name

        arguments:
            params_template: dictionary of template files
            params: dictionary of node sub-parameters (from a json file)
            name: pipeline name (default = "full_segment_pipe")

    Outputs:

    """
    # creating pipeline
    seg_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1', 'T2']),
        name='inputnode'
    )

    # preprocessing
    if 'data_preparation_pipe' in params.keys():
        print("data_preparation_pipe is in params")
        params_data_preparation_pipe = params["data_preparation_pipe"]
    else:
        print("*** data_preparation_pipe NOT in params")
        params_data_preparation_pipe = {}

    data_preparation_pipe = create_data_preparation_pipe(
        params_data_preparation_pipe)

    seg_pipe.connect(inputnode, 'T1', data_preparation_pipe, 'inputnode.T1')
    seg_pipe.connect(inputnode, 'T2', data_preparation_pipe, 'inputnode.T2')

    # full extract brain pipeline (correct_bias, denoising, extract brain)
    if 'brain_extraction_pipe' in params.keys():
        print("brain_extraction_pipe is in params")
        params_brain_extraction_pipe = params["brain_extraction_pipe"]
    else:
        print("*** brain_extraction_pipe NOT in params")
        params_brain_extraction_pipe = {}

    brain_extraction_pipe = create_brain_extraction_pipe(
        params=params_brain_extraction_pipe, params_template=params_template)

    seg_pipe.connect(data_preparation_pipe, 'denoise_T1.output_image',
                     brain_extraction_pipe, 'inputnode.preproc_T1')
    seg_pipe.connect(data_preparation_pipe, 'denoise_T2.output_image',
                     brain_extraction_pipe, 'inputnode.preproc_T2')

    # full_segment (restarting from the avg_align files)
    if "brain_segment_pipe" in params.keys():
        params_brain_segment_pipe = params["brain_segment_pipe"]

        brain_segment_pipe = create_brain_segment_from_mask_pipe(
            params_template=params_template,
            params=params_brain_segment_pipe)

        seg_pipe.connect(data_preparation_pipe, 'denoise_T1.output_image',
                         brain_segment_pipe, 'inputnode.preproc_T1')
        seg_pipe.connect(data_preparation_pipe, 'denoise_T2.output_image',
                         brain_segment_pipe, 'inputnode.preproc_T2')
        seg_pipe.connect(brain_extraction_pipe,
                         "extract_pipe.smooth_mask.out_file",
                         brain_segment_pipe, "inputnode.brain_mask")

    return seg_pipe
