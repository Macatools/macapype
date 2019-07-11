
import os
import shutil

import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni
import nipype.interfaces.ants as ants

from nipype.utils.misc import show_files
from nipype.utils.filemanip import split_filename as split_f

#fsl.FSLCommand.set_default_output_type('NIFTI')

from ..utils.misc import (print_val, print_nii_data)

from ..nodes.segment import (wrap_NMT_subject_align, wrap_antsAtroposN4,
    add_Nwarp)

def create_brain_segment_pipe(name = "brain_segment_pipe"):

    # creating pipeline
    brain_segment_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['extracted_T1']),
        name='inputnode')

    ########################### align subj to nmt


    ### NMT_subject_align
    NMT_subject_align= pe.Node(niu.Function(input_names = ["T1_file"], output_names = ["shft_aff_file", "warpinv_file", "transfo_file", "inv_transfo_file"], function = wrap_NMT_subject_align),name = 'NMT_subject_align')

    brain_segment_pipe.connect(inputnode,'extracted_T1',NMT_subject_align,"T1_file")

    ######################################### segmentation

    ### # STEP1 : align_masks

    nmt_dir="/hpc/meca/users/loh.k/macaque_preprocessing/NMT_v1.2/"

    NMT_file = os.path.join(nmt_dir,"NMT.nii.gz")
    NMT_brainmask_prob = os.path.join(nmt_dir,"masks","probabilisitic_segmentation_masks","NMT_brainmask_prob.nii.gz")
    NMT_brainmask = os.path.join(nmt_dir,"masks","anatomical_masks","NMT_brainmask.nii.gz")
    NMT_brainmask_CSF = os.path.join(nmt_dir,"masks","probabilisitic_segmentation_masks","NMT_segmentation_CSF.nii.gz")
    NMT_brainmask_GM = os.path.join(nmt_dir,"masks","probabilisitic_segmentation_masks","NMT_segmentation_GM.nii.gz")
    NMT_brainmask_WM = os.path.join(nmt_dir,"masks","probabilisitic_segmentation_masks","NMT_segmentation_WM.nii.gz")

    list_priors = [NMT_file, NMT_brainmask_prob, NMT_brainmask, NMT_brainmask_CSF, NMT_brainmask_GM, NMT_brainmask_WM]
    align_masks = pe.Node(afni.NwarpApply(),name = 'align_masks')
    align_masks.inputs.in_file= list_priors
    align_masks.inputs.out_file= add_Nwarp(list_priors)
    align_masks.inputs.interp="NN"
    align_masks.inputs.args="-overwrite"

    brain_segment_pipe.connect(NMT_subject_align,'shft_aff_file',align_masks,'master')
    brain_segment_pipe.connect(NMT_subject_align,'warpinv_file',align_masks,"warp")

    # STEP2: N4 intensity normalization over brain
    norm_intensity = pe.Node(ants.N4BiasFieldCorrection(),name = 'norm_intensity')
    norm_intensity.inputs.dimension = 3

    brain_segment_pipe.connect(NMT_subject_align,'shft_aff_file',norm_intensity,"input_image")

    ### #STEP 3: ants Atropos

    #make brainmask from brain image

    ### make_brainmask
    make_brainmask = pe.Node(fsl.Threshold(),name = 'make_brainmask')
    make_brainmask.inputs.thresh = 1
    make_brainmask.inputs.args = '-bin'

    brain_segment_pipe.connect(norm_intensity,'output_image',make_brainmask,'in_file')

    # Atropos
    seg_at = pe.Node(niu.Function(
        input_names = ["dimension","shft_aff_file", "brainmask_file","numberOfClasses","ex_prior"],
        output_names = ["out_files","seg_file","seg_post1_file","seg_post2_file", "seg_post3_file"],
        function = wrap_antsAtroposN4), name = 'seg_at')

    seg_at.inputs.dimension = 3
    seg_at.inputs.numberOfClasses = 3

    brain_segment_pipe.connect(NMT_subject_align,'shft_aff_file',seg_at,"shft_aff_file")
    brain_segment_pipe.connect(make_brainmask,'out_file',seg_at,"brainmask_file")
    brain_segment_pipe.connect(align_masks,('out_file',show_files),seg_at,"ex_prior")

    ### align result file to subj
    # first for brainmask
    align_brainmask = pe.Node(afni.Allineate(), name = "align_brainmask")
    align_brainmask.inputs.final_interpolation = "nearestneighbour"
    align_brainmask.inputs.overwrite = True
    align_brainmask.inputs.outputtype = "NIFTI_GZ"

    brain_segment_pipe.connect(make_brainmask,'out_file',align_brainmask,"in_file") # -source
    brain_segment_pipe.connect(inputnode,'extracted_T1',align_brainmask,"reference") # -base
    brain_segment_pipe.connect(NMT_subject_align,'inv_transfo_file',align_brainmask,"in_matrix") # -1Dmatrix_apply

    ## looping over the Segmentation files with MapNode
    # probleme avec la liste???? avec l'encodage unicode u''????

    #align_all_seg = pe.MapNode(interface = afni.Allineate(), iterfield = ["in_file"], name = "align_all_seg")
    #align_all_seg.inputs.final_interpolation = "nearestneighbour"
    #align_all_seg.inputs.overwrite = True
    #align_all_seg.inputs.outputtype = "NIFTI_GZ"

    #seg_pipe.connect(seg_at,('out_files',show_files),align_all_seg,"in_file") # -source
    #seg_pipe.connect(mult_T1,'out_file',align_all_seg,"reference") # -base
    #seg_pipe.connect(NMT_subject_align,'inv_transfo_file',align_all_seg,"in_matrix") # -1Dmatrix_apply

    ### align segmentation one by one:
    #seg
    align_seg = pe.Node(afni.Allineate(),  name = "align_seg")
    align_seg.inputs.final_interpolation = "nearestneighbour"
    align_seg.inputs.overwrite = True
    align_seg.inputs.outputtype = "NIFTI_GZ"

    brain_segment_pipe.connect(seg_at,("seg_file",show_files),align_seg,"in_file") # -source
    brain_segment_pipe.connect(inputnode,'extracted_T1',align_seg,"reference") # -base
    brain_segment_pipe.connect(NMT_subject_align,'inv_transfo_file',align_seg,"in_matrix") # -1Dmatrix_apply

    #seg_post1
    align_seg_post1 = pe.Node(afni.Allineate(),  name = "align_seg_post1")
    align_seg_post1.inputs.final_interpolation = "nearestneighbour"
    align_seg_post1.inputs.overwrite = True
    align_seg_post1.inputs.outputtype = "NIFTI_GZ"

    brain_segment_pipe.connect(seg_at,"seg_post1_file",align_seg_post1,"in_file") # -source
    brain_segment_pipe.connect(inputnode,'extracted_T1',align_seg_post1,"reference") # -base
    brain_segment_pipe.connect(NMT_subject_align,'inv_transfo_file',align_seg_post1,"in_matrix") # -1Dmatrix_apply

    #seg_post2
    align_seg_post2 = pe.Node(afni.Allineate(),  name = "align_seg_post2")
    align_seg_post2.inputs.final_interpolation = "nearestneighbour"
    align_seg_post2.inputs.overwrite = True
    align_seg_post2.inputs.outputtype = "NIFTI_GZ"

    brain_segment_pipe.connect(seg_at,"seg_post2_file",align_seg_post2,"in_file") # -source
    brain_segment_pipe.connect(inputnode,'extracted_T1',align_seg_post2,"reference") # -base
    brain_segment_pipe.connect(NMT_subject_align,'inv_transfo_file',align_seg_post2,"in_matrix") # -1Dmatrix_apply

    #seg_post3
    align_seg_post3 = pe.Node(afni.Allineate(),  name = "align_seg_post3")
    align_seg_post3.inputs.final_interpolation = "nearestneighbour"
    align_seg_post3.inputs.overwrite = True
    align_seg_post3.inputs.outputtype = "NIFTI_GZ"

    brain_segment_pipe.connect(seg_at,"seg_post3_file",align_seg_post3,"in_file") # -source
    brain_segment_pipe.connect(inputnode,'extracted_T1',align_seg_post3,"reference") # -base
    brain_segment_pipe.connect(NMT_subject_align,'inv_transfo_file',align_seg_post3,"in_matrix") # -1Dmatrix_apply

    return brain_segment_pipe
