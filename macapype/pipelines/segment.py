
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

from ..nodes.segment import (wrap_NMT_subject_align, wrap_antsAtroposN4_dirty,
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

from ..pipelines.denoise import create_cropped_denoised_pipe
from ..pipelines.correct_bias import create_masked_correct_bias_pipe

from ..utils.misc import get_elem

def create_full_segment_pipe(crop_list, sigma, name = "full_segment_pipe"):

    # creating pipeline
    brain_segment_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['preproc_T1','preproc_T2','brain_mask']),
        name='inputnode')

    crop_denoise_pipe = create_cropped_denoised_pipe(crop_list=crop_list)

    brain_segment_pipe.connect(inputnode,'preproc_T1',crop_denoise_pipe,"inputnode.preproc_T1")
    brain_segment_pipe.connect(inputnode,'preproc_T2',crop_denoise_pipe,"inputnode.preproc_T2")

    masked_correct_bias_pipe = create_masked_correct_bias_pipe(sigma = sigma)


    brain_segment_pipe.connect(crop_denoise_pipe,'denoise_T1.denoised_img_file',masked_correct_bias_pipe,"inputnode.preproc_T1")
    brain_segment_pipe.connect(crop_denoise_pipe,'denoise_T2.denoised_img_file',masked_correct_bias_pipe,"inputnode.preproc_T2")
    brain_segment_pipe.connect(inputnode,'brain_mask',masked_correct_bias_pipe,"inputnode.brain_mask")

    # STEP2: N4 intensity normalization over brain
    norm_intensity = pe.Node(ants.N4BiasFieldCorrection(),name = 'norm_intensity')
    norm_intensity.inputs.dimension = 3
    norm_intensity.inputs.bspline_fitting_distance = 200
    norm_intensity.inputs.n_iterations= [50,50,40,30]
    norm_intensity.inputs.convergence_threshold= 0.00000001
    norm_intensity.inputs.shrink_factor = 2
    norm_intensity.inputs.args = "r 0 --verbose 1"


    brain_segment_pipe.connect(masked_correct_bias_pipe,'restore_mask_T1.out_file',norm_intensity,"input_image")

    #### bin_norm_intensity
    bin_norm_intensity= pe.Node(fsl.UnaryMaths(), name = "bin_norm_intensity")
    bin_norm_intensity.inputs.operation = "bin"

    brain_segment_pipe.connect(norm_intensity,"output_image",bin_norm_intensity, "in_file")



    ########################### align subj to nmt


    ### NMT_subject_align
    NMT_subject_align= pe.Node(niu.Function(input_names = ["T1_file"], output_names = ["shft_aff_file", "warpinv_file", "transfo_file", "inv_transfo_file"], function = wrap_NMT_subject_align),name = 'NMT_subject_align')

    brain_segment_pipe.connect(norm_intensity,'output_image',NMT_subject_align,"T1_file")

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

    ### align template file to subject space

    ### align result file to subj
    # template
    #align_template = pe.Node(afni.Allineate(), name = "align_template", iterfield = ['in_file'])
    #align_template.inputs.final_interpolation = "nearestneighbour"
    #align_template.inputs.overwrite = True
    #align_template.inputs.outputtype = "NIFTI_GZ"

    #brain_segment_pipe.connect(align_masks,('out_file',get_elem, 0),align_template,"in_file") # -source
    #brain_segment_pipe.connect(norm_intensity,'output_image',align_template,"reference") # -base
    #brain_segment_pipe.connect(NMT_subject_align,'inv_transfo_file',align_template,"in_matrix") # -1Dmatrix_apply

    ## template_prior
    #align_template_prior = pe.Node(afni.Allineate(), name = "align_template_prior", iterfield = ['in_file'])
    #align_template_prior.inputs.final_interpolation = "nearestneighbour"
    #align_template_prior.inputs.overwrite = True
    #align_template_prior.inputs.outputtype = "NIFTI_GZ"

    #brain_segment_pipe.connect(align_masks,('out_file',get_elem, 1),align_template_prior,"in_file") # -source
    #brain_segment_pipe.connect(norm_intensity,'output_image',align_template_prior,"reference") # -base
    #brain_segment_pipe.connect(NMT_subject_align,'inv_transfo_file',align_template_prior,"in_matrix") # -1Dmatrix_apply

    ## brainmask
    #align_brainmask = pe.Node(afni.Allineate(), name = "align_brainmask", iterfield = ['in_file'])
    #align_brainmask.inputs.final_interpolation = "nearestneighbour"
    #align_brainmask.inputs.overwrite = True
    #align_brainmask.inputs.outputtype = "NIFTI_GZ"

    #brain_segment_pipe.connect(align_masks,('out_file',get_elem, 2),align_brainmask,"in_file") # -source
    #brain_segment_pipe.connect(norm_intensity,'output_image',align_brainmask,"reference") # -base
    #brain_segment_pipe.connect(NMT_subject_align,'inv_transfo_file',align_brainmask,"in_matrix") # -1Dmatrix_apply


    # seg_csf
    align_seg_csf = pe.Node(afni.Allineate(), name = "align_seg_csf", iterfield = ['in_file'])
    align_seg_csf.inputs.final_interpolation = "nearestneighbour"
    align_seg_csf.inputs.overwrite = True
    align_seg_csf.inputs.outputtype = "NIFTI_GZ"

    brain_segment_pipe.connect(align_masks,('out_file',get_elem, 3),align_seg_csf,"in_file") # -source
    brain_segment_pipe.connect(norm_intensity,'output_image',align_seg_csf,"reference") # -base
    brain_segment_pipe.connect(NMT_subject_align,'inv_transfo_file',align_seg_csf,"in_matrix") # -1Dmatrix_apply

    # seg_gm
    align_seg_gm = pe.Node(afni.Allineate(), name = "align_seg_gm", iterfield = ['in_file'])
    align_seg_gm.inputs.final_interpolation = "nearestneighbour"
    align_seg_gm.inputs.overwrite = True
    align_seg_gm.inputs.outputtype = "NIFTI_GZ"

    brain_segment_pipe.connect(align_masks,('out_file',get_elem, 4),align_seg_gm,"in_file") # -source
    brain_segment_pipe.connect(norm_intensity,'output_image',align_seg_gm,"reference") # -base
    brain_segment_pipe.connect(NMT_subject_align,'inv_transfo_file',align_seg_gm,"in_matrix") # -1Dmatrix_apply

    # seg_wm
    align_seg_wm = pe.Node(afni.Allineate(), name = "align_seg_wm", iterfield = ['in_file'])
    align_seg_wm.inputs.final_interpolation = "nearestneighbour"
    align_seg_wm.inputs.overwrite = True
    align_seg_wm.inputs.outputtype = "NIFTI_GZ"

    brain_segment_pipe.connect(align_masks,('out_file',get_elem, 5),align_seg_wm,"in_file") # -source
    brain_segment_pipe.connect(norm_intensity,'output_image',align_seg_wm,"reference") # -base
    brain_segment_pipe.connect(NMT_subject_align,'inv_transfo_file',align_seg_wm,"in_matrix") # -1Dmatrix_apply

    ### #STEP 3: ants Atropos

    # Atropos
    seg_at = pe.Node(niu.Function(
        input_names = ["dimension","brain_file", "brainmask_file","numberOfClasses","ex_prior1","ex_prior2","ex_prior3"],
        output_names = ["out_files","seg_file","seg_post1_file","seg_post2_file", "seg_post3_file"],
        function = wrap_antsAtroposN4_dirty), name = 'seg_at')

    seg_at.inputs.dimension = 3
    seg_at.inputs.numberOfClasses = 3

    brain_segment_pipe.connect(norm_intensity,'output_image',seg_at,"brain_file")
    brain_segment_pipe.connect(bin_norm_intensity,'out_file',seg_at,"brainmask_file")
    brain_segment_pipe.connect(align_seg_csf,'out_file',seg_at,"ex_prior1")
    brain_segment_pipe.connect(align_seg_gm,'out_file',seg_at,"ex_prior2")
    brain_segment_pipe.connect(align_seg_wm,'out_file',seg_at,"ex_prior3")

    return brain_segment_pipe
