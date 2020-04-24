
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from macapype.nodes.correct_bias import T1xT2BiasFieldCorrection
from macapype.nodes.register import IterREGBET

from .preproc import create_preproc_pipe

from .segment import (create_old_segment_pipe,
                      create_segment_atropos_pipe)

from .denoise import create_denoised_pipe
from .correct_bias import (create_masked_correct_bias_pipe,
                           create_correct_bias_pipe)

from .register import create_register_NMT_pipe

from .extract_brain import create_extract_pipe

from macapype.utils.misc import gunzip


###############################################################################
def create_full_segment_pnh_T1xT2(params_template, params={},
                                  name='T1xT2_segmentation_pipeline'):
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
    if 'preproc_pipe' in params.keys():
        print("preproc_pipe is in params")
        params_preproc_pipe = params["preproc_pipe"]
    else:
        print("*** preproc_pipe NOT in params")
        params_preproc_pipe = {}

    preproc_pipe = create_preproc_pipe(params_preproc_pipe)

    seg_pipe.connect(inputnode, 'T1', preproc_pipe, 'inputnode.T1')
    seg_pipe.connect(inputnode, 'T2', preproc_pipe, 'inputnode.T2')

    # Brain extraction + Cropping
    """
    if "T1xT2BET" in params.keys():
        m = params["T1xT2BET"]["m"]
        aT2 = params["T1xT2BET"]["aT2"]
        c = params["T1xT2BET"]["c"]
        n = params["T1xT2BET"]["n"]
        f = params["T1xT2BET"]["f"]
        g = params["T1xT2BET"]["g"]
    else:
        m = True
        aT2 = True
        c = 10
        n = 2
        f = 0.0
        g = 0.5
    bet = pe.Node(T1xT2BET(m=m, aT2=aT2, c=c, n=n, f=f, g=g), name='bet')

    seg_pipe.connect(inputnode, ('T1', average_align), bet, 't1_file')
    seg_pipe.connect(inputnode, ('T2', average_align), bet, 't2_file')
    """
    # Bias correction of cropped images
    if "debias" in params.keys():
        s = params["debias"]["s"]
    else:
        s = 4

    debias = pe.Node(T1xT2BiasFieldCorrection(s=s), name='debias')
    """
    seg_pipe.connect(bet, 't1_cropped_file', debias, 't1_file')
    seg_pipe.connect(bet, 't2_cropped_file', debias, 't2_file')
    seg_pipe.connect(bet, 'mask_file', debias, 'b')
    """

    seg_pipe.connect(preproc_pipe, 'bet_crop.t1_cropped_file',
                     debias, 't1_file')
    seg_pipe.connect(preproc_pipe, 'bet_crop.t2_cropped_file',
                     debias, 't2_file')
    seg_pipe.connect(preproc_pipe, 'bet_crop.mask_file', debias, 'b')

    # Iterative registration to the INIA19 template

    reg = pe.Node(IterREGBET(), name='reg')
    reg.inputs.refb_file = params_template["template_brain"]

    if "reg" in params.keys() and "n" in params["reg"].keys():
        reg.inputs.n = params["reg"]["n"]

    if "reg" in params.keys() and "m" in params["reg"].keys():
        reg.inputs.m = params["reg"]["m"]

    if "reg" in params.keys() and "dof" in params["reg"].keys():
        reg.inputs.dof = params["reg"]["dof"]

    seg_pipe.connect(debias, 't1_debiased_file', reg, 'inw_file')
    seg_pipe.connect(debias, 't1_debiased_brain_file', reg, 'inb_file')

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
# Kepkee

def create_brain_extraction_pipe(params_template, params={}, name="brain_extraction_pipe"):
        """
    Description:


    new version (as it is now)
    - preproc (avg and align on the fly, cropping from T1xT2BET, bet is optional) # noqa
    - correct_bias
    - denoise
    - extract_brain
    - segment from mask (see create_full_segment_from_mask_pipe):

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
    extract_pipe = pe.Workflow(name=name)

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

    # denoising
    if "denoised_pipe" in params.keys():  # so far, unused
        params_denoised_pipe = params["denoised_pipe"]
    else:
        params_denoised_pipe = {}

    denoise_pipe = create_denoised_pipe(params=params_denoised_pipe)

    brain_extraction_pipe.connect(correct_bias_pipe, "restore_T1.out_file",
                     denoise_pipe, 'inputnode.preproc_T1')
    brain_extraction_pipe.connect(correct_bias_pipe, "restore_T2.out_file",
                     denoise_pipe, 'inputnode.preproc_T2')

    # brain extraction
    if "extract_pipe" in params.keys():  # so far, unused
        params_extract_pipe = params["extract_pipe"]

    else:
        params_extract_pipe = {}

    extract_pipe = create_extract_pipe(
        params_template=params_template,
        params=params_extract_pipe)

    brain_extraction_pipe.connect(denoise_pipe, 'denoise_T1.output_image',
                     extract_pipe, "inputnode.restore_T1")
    brain_extraction_pipe.connect(denoise_pipe, 'denoise_T2.output_image',
                     extract_pipe, "inputnode.restore_T2")

    return brain_extraction_pipe


def create_full_segment_from_mask_pipe(
        params_template, params={}, name="full_segment_from_mask_pipe"):
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

    denoise_pipe = create_denoised_pipe()

    brain_segment_pipe.connect(inputnode, 'preproc_T1',
                               denoise_pipe, "inputnode.preproc_T1")
    brain_segment_pipe.connect(inputnode, 'preproc_T2',
                               denoise_pipe, "inputnode.preproc_T2")

    # correcting for bias T1/T2, but this time with a mask
    if "masked_correct_bias_pipe" in params.keys():
        params_masked_correct_bias_pipe = params["masked_correct_bias_pipe"]
    else:
        params_masked_correct_bias_pipe = {}

    masked_correct_bias_pipe = create_masked_correct_bias_pipe(
        params=params_masked_correct_bias_pipe)

    brain_segment_pipe.connect(
        denoise_pipe, 'denoise_T1.output_image',
        masked_correct_bias_pipe, "inputnode.preproc_T1")
    brain_segment_pipe.connect(
        denoise_pipe, 'denoise_T2.output_image',
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
        params_template, params={}, name="segment_pnh_subpipes"):
    """
    Description: Segment T1 (using T2 for bias correction) .

    new version (as it is now)
    - preproc (avg and align on the fly, cropping from T1xT2BET, bet is optional) # noqa
    - correct_bias
    - denoise
    - extract_brain
    - segment from mask (see create_full_segment_from_mask_pipe):

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
    seg_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1', 'T2']),
        name='inputnode'
    )

    # preprocessing
    if 'brain_preproc_pipe' in params.keys():
        print("brain_preproc_pipe is in params")
        params_brain_preproc_pipe = params["brain_preproc_pipe"]
    else:
        print("*** brain_preproc_pipe NOT in params")
        params_brain_preproc_pipe = {}

    brain_preproc_pipe = create_brain_preproc_pipe(params_brain_preproc_pipe)

    seg_pipe.connect(inputnode, 'T1', preproc_pipe, 'inputnode.T1')
    seg_pipe.connect(inputnode, 'T2', preproc_pipe, 'inputnode.T2')

    # full extract brain pipeline (correct_bias, denoising, extract brain)
    if 'brain_extraction_pipe' in params.keys():
        print("brain_extraction_pipe is in params")
        params_brain_extraction_pipe = params["brain_extraction_pipe"]
    else:
        print("*** brain_extraction_pipe NOT in params")
        params_brain_extraction_pipe = {}

    brain_extraction_pipe = create_brain_extraction_pipe(
        params=params_extract_pipe, params_template=params_template)

    if "bet_crop" in params['brain_preproc_pipe'].keys():
        seg_pipe.connect(brain_preproc_pipe, 'bet_crop.t1_cropped_file',
                         brain_extraction_pipe, 'inputnode.preproc_T1')
        seg_pipe.connect(brain_preproc_pipe, 'bet_crop.t2_cropped_file',
                         brain_extraction_pipe, 'inputnode.preproc_T2')
    elif "crop" in params['brain_preproc_pipe'].keys():
        seg_pipe.connect(brain_preproc_pipe, 'crop_bb_T1.roi_file',
                         brain_extraction_pipe, 'inputnode.preproc_T1')
        seg_pipe.connect(brain_preproc_pipe, 'crop_bb_T2.roi_file',
                         brain_extraction_pipe, 'inputnode.preproc_T2')

    # full_segment (restarting from the avg_align files)
    if "brain_segment_pipe" in params.keys():
        params_brain_segment_pipe = params["brain_segment_pipe"]

        brain_segment_pipe = create_full_segment_from_mask_pipe(
            params_template=params_template,
            params=params_brain_segment_pipe)

        if "bet_crop" in params['preproc_pipe'].keys():
            seg_pipe.connect(preproc_pipe, 'bet_crop.t1_cropped_file',
                             brain_segment_pipe, 'inputnode.preproc_T1')
            seg_pipe.connect(preproc_pipe, 'bet_crop.t2_cropped_file',
                             brain_segment_pipe, 'inputnode.preproc_T2')
        elif "crop" in params['preproc_pipe'].keys():
            seg_pipe.connect(preproc_pipe, 'crop_bb_T1.roi_file',
                             brain_segment_pipe, 'inputnode.preproc_T1')
            seg_pipe.connect(preproc_pipe, 'crop_bb_T2.roi_file',
                             brain_segment_pipe, 'inputnode.preproc_T2')

        seg_pipe.connect(brain_extraction_pipe, "extract_pipe.smooth_mask.out_file",
                         brain_segment_pipe, "inputnode.brain_mask")

    return seg_pipe
