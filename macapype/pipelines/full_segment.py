
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl


from macapype.nodes.bash_regis import (T1xT2BET, T1xT2BiasFieldCorrection,
                                      IterREGBET)

from macapype.nodes.preproc import average_align

from .extract_brain import create_old_segment_extraction_pipe

from .denoise import create_denoised_pipe
from .correct_bias import create_masked_correct_bias_pipe
from .register import create_register_NMT_pipe
from .segment import create_segment_atropos_pipe

from macapype.utils.misc import gunzip

###############################################################################
# Regis
def create_full_segment_pnh_T1xT2(brain_template, priors,
                             name='T1xT2_segmentation_pipeline'):
    print(brain_template)
    print(priors)
    print("node name: ", name)

    # Creating pipeline
    seg_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1','T2']),
        name='inputnode'
    )

    # Brain extraction (unused) + Cropping
    bet = pe.Node(T1xT2BET(m=True, aT2=True, c=10), name='bet')
    bet.n = 2
    seg_pipe.connect(inputnode, ('T1', average_align), bet, 't1_file')
    seg_pipe.connect(inputnode, ('T2', average_align), bet, 't2_file')

    # Bias correction of cropped images
    debias = pe.Node(T1xT2BiasFieldCorrection(), name='debias')
    seg_pipe.connect(bet, 't1_cropped_file', debias, 't1_file')
    seg_pipe.connect(bet, 't2_cropped_file', debias, 't2_file')
    seg_pipe.connect(bet, 'mask_file', debias, 'b')

    # Iterative registration to the INIA19 template
    reg = pe.Node(IterREGBET(), name='reg')
    reg.inputs.refb_file = brain_template
    seg_pipe.connect(debias, 't1_debiased_file', reg, 'inw_file')
    seg_pipe.connect(debias, 't1_debiased_brain_file', reg, 'inb_file')

    # Compute brain mask using old_segment of SPM and postprocessing on
    # tissues' masks
    extract_brain = create_old_segment_extraction_pipe(priors)
    seg_pipe.connect(reg, ('warp_file', gunzip), extract_brain, 'inputnode.T1')

    return seg_pipe


###############################################################################
# Kepkee
def create_full_segment_pipe(sigma, nmt_dir, name="full_segment_pipe"):

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
    masked_correct_bias_pipe = create_masked_correct_bias_pipe(sigma=sigma)

    # with denoise
    brain_segment_pipe.connect(
        denoise_pipe, 'denoise_T1.output_image',
        masked_correct_bias_pipe, "inputnode.preproc_T1")
    brain_segment_pipe.connect(
        denoise_pipe, 'denoise_T2.output_image',
        masked_correct_bias_pipe, "inputnode.preproc_T2")

    # segment
    brain_segment_pipe.connect(inputnode, 'brain_mask',
                               masked_correct_bias_pipe,
                               "inputnode.brain_mask")

    # register NMT template, template mask and priors to subject T1
    register_NMT_pipe = create_register_NMT_pipe(nmt_dir=nmt_dir)

    brain_segment_pipe.connect(
        masked_correct_bias_pipe, 'restore_mask_T1.out_file',
        register_NMT_pipe, "inputnode.T1_file")

    # ants Atropos
    segment_atropos_pipe = create_segment_atropos_pipe(dimension=3,
                                                       numberOfClasses=3)

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

