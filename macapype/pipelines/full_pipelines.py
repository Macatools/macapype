
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from ..utils.utils_nodes import NodeParams, parse_key

from macapype.nodes.correct_bias import T1xT2BiasFieldCorrection
from macapype.nodes.register import IterREGBET

from .prepare import (create_data_preparation_pipe)

from .segment import (create_old_segment_pipe,
                      create_segment_atropos_pipe)

from .correct_bias import (create_masked_correct_bias_pipe,
                           create_correct_bias_pipe)

from .register import create_register_NMT_pipe, create_multi_register_NMT_pipe

from .extract_brain import create_extract_pipe

from macapype.utils.misc import gunzip


###############################################################################
# SPM based segmentation (from: Régis Trapeau)
def create_full_T1xT2_segment_pnh_subpipes(
        params_template, params={}, name='full_T1xT2_segment_pnh_subpipes'):
    """ Description: SPM based segmentation pipeline from T1w and T2w images

        - data_preparation_pipe:
            - avg_align
            - deoblique,
            - reorient if needed
            - bet_crop (brain extraction and crop) -> mask
            - denoise
        - T1xT2BiasFieldCorrection using mask -> debias
        - IterREGBET -> registration to template file
        - old_segment_pipe

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

    # Bias correction of cropped images
    debias = NodeParams(T1xT2BiasFieldCorrection(), name='debias')
    debias.load_inputs_from_dict(params["debias"])

    seg_pipe.connect(data_preparation_pipe, 'denoise_T1.output_image',
                     debias, 't1_file')
    seg_pipe.connect(data_preparation_pipe, 'denoise_T2.output_image',
                     debias, 't2_file')
    seg_pipe.connect(data_preparation_pipe, 'bet_crop.mask_file',
                     debias, 'b')

    # Iterative registration to the INIA19 template
    reg = NodeParams(IterREGBET(), name='reg')
    reg.inputs.refb_file = params_template["template_brain"]
    reg.load_inputs_from_dict(params["reg"])

    seg_pipe.connect(debias, 't1_debiased_file', reg, 'inw_file')
    seg_pipe.connect(debias, 't1_debiased_brain_file',
                     reg, 'inb_file')

    # Compute brain mask using old_segment of SPM and postprocessing on
    # tissues' masks
    if "old_segment_pipe" in params.keys():
        params_old_segment_pipe = params["old_segment_pipe"]
    else:
        params_old_segment_pipe = {}

    old_segment_pipe = create_old_segment_pipe(
        params_template, params=params_old_segment_pipe)

    seg_pipe.connect(reg, ('warp_file', gunzip),
                     old_segment_pipe, 'inputnode.T1')

    return seg_pipe


###############################################################################
# ANTS based segmentation (from: Kepkee Loh)

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

###############################################################################
# multi / indiv_params
###############################################################################
# same as before, but with indiv_params
def create_brain_extraction_pipe(params_template, params={},
                                       name="brain_extraction_pipe"):
    """ Description: ANTS based segmentation pipeline using T1w and T2w images


    - correct_bias
    - denoise
    - extract_brain
    Inputs:

        inputnode:
            preproc_T1: preprocessed T1 file name
            preproc_T2: preprocessed T2 file name

            indiv_params (opt): dict with individuals parameters for some nodes


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
        niu.IdentityInterface(fields=['preproc_T1', 'preproc_T2',
                                      'indiv_params']),
        name='inputnode')

    # Correct_bias_T1_T2
    correct_bias_pipe = create_correct_bias_pipe(
        params=parse_key(params, "correct_bias_pipe"))

    brain_extraction_pipe.connect(inputnode, 'preproc_T1',
                                  correct_bias_pipe, 'inputnode.preproc_T1')
    brain_extraction_pipe.connect(inputnode, 'preproc_T2',
                                  correct_bias_pipe, 'inputnode.preproc_T2')

    # brain extraction
    extract_pipe = create_extract_pipe(
        params_template=params_template,
        params=parse_key(params, "extract_pipe"))

    brain_extraction_pipe.connect(correct_bias_pipe, "restore_T1.out_file",
                                  extract_pipe, "inputnode.restore_T1")
    brain_extraction_pipe.connect(correct_bias_pipe, "restore_T2.out_file",
                                  extract_pipe, "inputnode.restore_T2")
    brain_extraction_pipe.connect(inputnode, "indiv_params",
                                  extract_pipe, "inputnode.indiv_params")

    return brain_extraction_pipe


def create_multi_brain_segment_from_mask_pipe(
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
            fields=['preproc_T1', 'preproc_T2', 'brain_mask', 'indiv_params']),
        name='inputnode')

    # correcting for bias T1/T2, but this time with a mask
    masked_correct_bias_pipe = create_masked_correct_bias_pipe(
        params=parse_key(params, "masked_correct_bias_pipe"))

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
    register_NMT_pipe = create_multi_register_NMT_pipe(
        params_template=params_template,
        params=parse_key(params, "register_NMT_pipe"))

    brain_segment_pipe.connect(
        masked_correct_bias_pipe, 'restore_mask_T1.out_file',
        register_NMT_pipe, "inputnode.T1")
    brain_segment_pipe.connect(
        inputnode, 'indiv_params',
        register_NMT_pipe, "inputnode.indiv_params")

    # ants Atropos
    segment_atropos_pipe = create_segment_atropos_pipe(
        params=parse_key(params, "segment_atropos_pipe"))

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


def create_full_segment_pnh_subpipes(
        params_template, params={}, name="full_segment_pnh_subpipes"):
    """Description: Segment T1 (using T2 for bias correction) .

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
            indiv_params (opt): dict with individuals parameters for some nodes

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
        niu.IdentityInterface(fields=['T1', 'T2', 'indiv_params']),
        name='inputnode'
    )

    # preprocessing
    if 'data_preparation_pipe' in params.keys():
        print("data_preparation_pipe is in params")
        params_data_preparation_pipe =
    else:
        print("*** data_preparation_pipe NOT in params")
        params_data_preparation_pipe = {}

    data_preparation_pipe = create_data_preparation_pipe(
        params=parse_key(params, "data_preparation_pipe"))

    seg_pipe.connect(inputnode, 'T1', data_preparation_pipe, 'inputnode.T1')
    seg_pipe.connect(inputnode, 'T2', data_preparation_pipe, 'inputnode.T2')

    seg_pipe.connect(inputnode, 'indiv_params',
                     data_preparation_pipe, 'inputnode.indiv_params')

    # full extract brain pipeline (correct_bias, denoising, extract brain)
    brain_extraction_pipe = create_brain_extraction_pipe(
        params=parse_key(params, "brain_extraction_pipe"),
        params_template=params_template)

    seg_pipe.connect(data_preparation_pipe, 'denoise_T1.output_image',
                     brain_extraction_pipe, 'inputnode.preproc_T1')
    seg_pipe.connect(data_preparation_pipe, 'denoise_T2.output_image',
                     brain_extraction_pipe, 'inputnode.preproc_T2')
    seg_pipe.connect(inputnode, 'indiv_params',
                     brain_extraction_pipe, 'inputnode.indiv_params')

    ## full_segment (restarting from the avg_align files)
    #if "brain_segment_pipe" in params.keys():
        #params_brain_segment_pipe = params["brain_segment_pipe"]

        #brain_segment_pipe = create_multi_brain_segment_from_mask_pipe(
            #params_template=params_template,
            #params=params_brain_segment_pipe)

        #seg_pipe.connect(data_preparation_pipe, 'denoise_T1.output_image',
                         #brain_segment_pipe, 'inputnode.preproc_T1')
        #seg_pipe.connect(data_preparation_pipe, 'denoise_T2.output_image',
                         #brain_segment_pipe, 'inputnode.preproc_T2')
        #seg_pipe.connect(brain_extraction_pipe,
                         #"extract_pipe.smooth_mask.out_file",
                         #brain_segment_pipe, "inputnode.brain_mask")

        #seg_pipe.connect(inputnode, 'indiv_params',
                         #brain_segment_pipe, 'inputnode.indiv_params')

    return seg_pipe
