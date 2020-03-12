
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl

from ..nodes.segment import wrap_antsAtroposN4_dirty

from .denoise import create_denoised_pipe
from .correct_bias import create_masked_correct_bias_pipe
from .register import create_register_NMT_pipe


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


def create_segment_atropos_pipe(dimension, numberOfClasses,
                                name="segment_atropos_pipe"):

    # creating pipeline
    segment_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=["brain_file", "gm_prior_file", "wm_prior_file",
                    "csf_prior_file"]),
        name='inputnode')

    # bin_norm_intensity (a cheat from Kepkee if I understood well!)
    bin_norm_intensity = pe.Node(fsl.UnaryMaths(), name="bin_norm_intensity")
    bin_norm_intensity.inputs.operation = "bin"

    segment_pipe.connect(inputnode, "brain_file",
                         bin_norm_intensity, "in_file")

    # STEP 3: ants Atropos
    # Atropos
    seg_at = pe.Node(niu.Function(
        input_names=["dimension", "brain_file", "brainmask_file",
                     "numberOfClasses", "ex_prior1", "ex_prior2", "ex_prior3"],
        output_names=["out_files", "seg_file", "seg_post1_file",
                      "seg_post2_file", "seg_post3_file"],
        function=wrap_antsAtroposN4_dirty), name='seg_at')

    seg_at.inputs.dimension = dimension
    seg_at.inputs.numberOfClasses = numberOfClasses

    segment_pipe.connect(inputnode, 'brain_file', seg_at, "brain_file")
    segment_pipe.connect(bin_norm_intensity, 'out_file',
                         seg_at, "brainmask_file")

    # TODO
    # was like this before (1 -> csf, 2 -> gm, 3 -> wm, to check)
    segment_pipe.connect(inputnode, 'csf_prior_file', seg_at, "ex_prior1")
    segment_pipe.connect(inputnode, 'gm_prior_file', seg_at, "ex_prior2")
    segment_pipe.connect(inputnode, 'wm_prior_file', seg_at, "ex_prior3")

    return segment_pipe

