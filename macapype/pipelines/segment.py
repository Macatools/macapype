
import os
import shutil

import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni
import nipype.interfaces.ants as ants

from nipype.utils.filemanip import split_filename as split_f

#fsl.FSLCommand.set_default_output_type('NIFTI')

from ..utils.misc import (show_files, print_val, print_nii_data)

from ..nodes.segment import wrap_antsAtroposN4_dirty

from .denoise import create_denoised_pipe
from .correct_bias import create_masked_correct_bias_pipe
from .register import create_register_NMT_pipe


def create_full_segment_pipe(sigma, nmt_dir,
                             name="full_segment_pipe"):

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



    ############### correcting for bias T1/T2, but this time with a mask ######
    masked_correct_bias_pipe = create_masked_correct_bias_pipe(sigma=sigma)

    ## without denoise
    #brain_segment_pipe.connect(
        #inputnode, 'preproc_T1',
        #masked_correct_bias_pipe, "inputnode.preproc_T1")

    #brain_segment_pipe.connect(
        #inputnode, 'preproc_T1',
        #masked_correct_bias_pipe, "inputnode.preproc_T2")

    # with denoise
    brain_segment_pipe.connect(
        denoise_pipe,'denoise_T1.output_image',
        masked_correct_bias_pipe, "inputnode.preproc_T1")
    brain_segment_pipe.connect(
        denoise_pipe,'denoise_T2.output_image',
        masked_correct_bias_pipe, "inputnode.preproc_T2")

    # segment
    brain_segment_pipe.connect(inputnode, 'brain_mask',
                               masked_correct_bias_pipe,
                               "inputnode.brain_mask")

    ############# register NMT template, template mask and priors to subject T1
    register_NMT_pipe = create_register_NMT_pipe(nmt_dir = nmt_dir)

    brain_segment_pipe.connect(
        masked_correct_bias_pipe, 'restore_mask_T1.out_file',
        register_NMT_pipe, "inputnode.T1_file")

    ######################################### ants Atropos ####################
    segment_atropos_pipe = create_segment_atropos_pipe(dimension = 3,
                                                       numberOfClasses = 3)

    brain_segment_pipe.connect(
        register_NMT_pipe, 'norm_intensity.output_image',
        segment_atropos_pipe, "inputnode.brain_file")

    brain_segment_pipe.connect(register_NMT_pipe, 'align_seg_csf.out_file',
                               segment_atropos_pipe, "inputnode.csf_prior_file")
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
            fields=["brain_file", "gm_prior_file", "wm_prior_file", "csf_prior_file"]),
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

    segment_pipe.connect(inputnode, 'brain_file',
                               seg_at, "brain_file")
    segment_pipe.connect(bin_norm_intensity, 'out_file',
                               seg_at, "brainmask_file")

    #TODO ## was like this before (1 -> csf, 2 -> gm, 3 -> wm, to check)
    segment_pipe.connect(inputnode, 'csf_prior_file', seg_at, "ex_prior1")
    segment_pipe.connect(inputnode, 'gm_prior_file', seg_at, "ex_prior2")
    segment_pipe.connect(inputnode, 'wm_prior_file', seg_at, "ex_prior3")

    return segment_pipe



# Previous version of Kepkee's pipeline
# 04/2019 - NMT_align subj -> NMT, then Atropos, and alignement of result back in subject space
"""
def create_brain_segment_pipe(NMT_file, NMT_brainmask_prob, NMT_brainmask,
                              NMT_brainmask_CSF, NMT_brainmask_GM,
                              NMT_brainmask_WM, name = "brain_segment_pipe"):

    # creating pipeline
    brain_segment_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['extracted_T1']),
        name='inputnode')

    ############################ align subj to nmt


    #### NMT_subject_align
    #NMT_subject_align= pe.Node(niu.Function(input_names = ["T1_file"], output_names = ["shft_aff_file", "warpinv_file", "transfo_file", "inv_transfo_file"], function = wrap_NMT_subject_align), name = 'NMT_subject_align')

    #brain_segment_pipe.connect(inputnode, 'extracted_T1', NMT_subject_align, "T1_file")

    ########################################## segmentation

    #### # STEP1 : align_masks

    #list_priors = [NMT_file, NMT_brainmask_prob, NMT_brainmask, NMT_brainmask_CSF, NMT_brainmask_GM, NMT_brainmask_WM]
    #align_masks = pe.Node(afni.NwarpApply(), name = 'align_masks')
    #align_masks.inputs.in_file= list_priors
    #align_masks.inputs.out_file= add_Nwarp(list_priors)
    #align_masks.inputs.interp="NN"
    #align_masks.inputs.args="-overwrite"

    #brain_segment_pipe.connect(NMT_subject_align, 'shft_aff_file', align_masks, 'master')
    #brain_segment_pipe.connect(NMT_subject_align, 'warpinv_file', align_masks, "warp")

    ## STEP2: N4 intensity normalization over brain
    #norm_intensity = pe.Node(ants.N4BiasFieldCorrection(), name = 'norm_intensity')
    #norm_intensity.inputs.dimension = 3

    #brain_segment_pipe.connect(NMT_subject_align, 'shft_aff_file', norm_intensity, "input_image")

    #### #STEP 3: ants Atropos

    ##make brainmask from brain image

    #### make_brainmask
    #make_brainmask = pe.Node(fsl.Threshold(), name = 'make_brainmask')
    #make_brainmask.inputs.thresh = 1
    #make_brainmask.inputs.args = '-bin'

    #brain_segment_pipe.connect(norm_intensity, 'output_image', make_brainmask, 'in_file')

    ## Atropos
    #seg_at = pe.Node(niu.Function(
        #input_names = ["dimension", "shft_aff_file", "brainmask_file", "numberOfClasses", "ex_prior"],
        #output_names = ["out_files", "seg_file", "seg_post1_file", "seg_post2_file", "seg_post3_file"],
        #function = wrap_antsAtroposN4), name = 'seg_at')

    #seg_at.inputs.dimension = 3
    #seg_at.inputs.numberOfClasses = 3

    #brain_segment_pipe.connect(NMT_subject_align, 'shft_aff_file', seg_at, "shft_aff_file")
    #brain_segment_pipe.connect(make_brainmask, 'out_file', seg_at, "brainmask_file")
    #brain_segment_pipe.connect(align_masks, ('out_file', show_files), seg_at, "ex_prior")

    #### align result file to subj
    ## first for brainmask
    #align_brainmask = pe.Node(afni.Allineate(), name = "align_brainmask")
    #align_brainmask.inputs.final_interpolation = "nearestneighbour"
    #align_brainmask.inputs.overwrite = True
    #align_brainmask.inputs.outputtype = "NIFTI_GZ"

    #brain_segment_pipe.connect(make_brainmask, 'out_file', align_brainmask, "in_file") # -source
    #brain_segment_pipe.connect(inputnode, 'extracted_T1', align_brainmask, "reference") # -base
    #brain_segment_pipe.connect(NMT_subject_align, 'inv_transfo_file', align_brainmask, "in_matrix") # -1Dmatrix_apply

    ## align segmentation one by one:
    ## seg
    #align_seg = pe.Node(afni.Allineate(), name = "align_seg")
    #align_seg.inputs.final_interpolation = "nearestneighbour"
    #align_seg.inputs.overwrite = True
    #align_seg.inputs.outputtype = "NIFTI_GZ"

    #brain_segment_pipe.connect(seg_at, ("seg_file", show_files),
                               #align_seg, "in_file") # -source
    #brain_segment_pipe.connect(inputnode, 'extracted_T1',
                               #align_seg, "reference") # -base
    #brain_segment_pipe.connect(NMT_subject_align, 'inv_transfo_file',
                               #align_seg, "in_matrix") # -1Dmatrix_apply

    ## seg_post1
    #align_seg_post1 = pe.Node(afni.Allineate(), name="align_seg_post1")
    #align_seg_post1.inputs.final_interpolation = "nearestneighbour"
    #align_seg_post1.inputs.overwrite = True
    #align_seg_post1.inputs.outputtype = "NIFTI_GZ"

    #brain_segment_pipe.connect(seg_at, "seg_post1_file",
                               #align_seg_post1, "in_file")  # -source
    #brain_segment_pipe.connect(inputnode, 'extracted_T1',
                               #align_seg_post1, "reference")  # -base
    #brain_segment_pipe.connect(NMT_subject_align, 'inv_transfo_file',
                               #align_seg_post1, "in_matrix")  # -1Dmatrix_apply

    ## seg_post2
    #align_seg_post2 = pe.Node(afni.Allineate(), name="align_seg_post2")
    #align_seg_post2.inputs.final_interpolation = "nearestneighbour"
    #align_seg_post2.inputs.overwrite = True
    #align_seg_post2.inputs.outputtype = "NIFTI_GZ"

    #brain_segment_pipe.connect(seg_at, "seg_post2_file",
                               #align_seg_post2, "in_file")  # -source
    #brain_segment_pipe.connect(inputnode, 'extracted_T1',
                               #align_seg_post2, "reference")  # -base
    #brain_segment_pipe.connect(NMT_subject_align, 'inv_transfo_file',
                               #align_seg_post2, "in_matrix")  # -1Dmatrix_apply

    ## seg_post3
    #align_seg_post3 = pe.Node(afni.Allineate(), name="align_seg_post3")
    #align_seg_post3.inputs.final_interpolation = "nearestneighbour"
    #align_seg_post3.inputs.overwrite = True
    #align_seg_post3.inputs.outputtype = "NIFTI_GZ"

    #brain_segment_pipe.connect(seg_at, "seg_post3_file",
                               #align_seg_post3, "in_file")  # -source
    #brain_segment_pipe.connect(inputnode, 'extracted_T1',
                               #align_seg_post3, "reference")  # -base
    #brain_segment_pipe.connect(NMT_subject_align, 'inv_transfo_file',
                               #align_seg_post3, "in_matrix")  # -1Dmatrix_apply

    #return brain_segment_pipe
"""
