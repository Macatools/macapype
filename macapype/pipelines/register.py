
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni
import nipype.interfaces.ants as ants

from ..utils.misc import get_elem

#from ..nodes.register import (interative_flirt, wrap_NMT_subject_align,
                              #add_Nwarp)

from ..nodes.register import (interative_flirt, NMTSubjectAlign,
                              NwarpApplyPriors)



def create_iterative_register_pipe(
    template_file, template_brain_file, template_mask_file, gm_prob_file,
    wm_prob_file, csf_prob_file, n_iter, name = "register_pipe"):


    """
    Registration of template (NMT or other) accroding to Regis:
    - The iterative FLIRT is between NMT_SS and subject's anat after a quick skull-stripping
    but the anat is more and more refined to corresponds to the brain
    - there is also a FNIRT done once, for comparison of the quality of the template on the subject's brain

    """
    register_pipe = pe.Workflow(name = name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['anat_file_BET','anat_file']),
        name='inputnode')

    # register node
    register = pe.Node(
        niu.Function(input_names=["anat_file","anat_file_BET","template_brain_file",
                                  "template_mask_file",'n_iter'],
                     output_names=["anat_file_brain", "template_to_anat_file"],
                     function=interative_flirt),
        name = "register")

    register.inputs.template_brain_file = template_brain_file
    register.inputs.template_mask_file = template_mask_file
    register.inputs.n_iter = n_iter

    register_pipe.connect(inputnode, 'anat_file', register, 'anat_file')
    register_pipe.connect(inputnode, 'anat_file_BET', register, "anat_file_BET")

    # apply transfo over the 3 tissues:

    # gm
    register_gm = pe.Node(fsl.ApplyXFM(), name = "register_gm")

    register_gm.inputs.in_file = gm_prob_file
    register_gm.inputs.apply_xfm = True
    register_gm.inputs.interp = "nearestneighbour"
    register_gm.inputs.output_type = "NIFTI" # for SPM segment


    register_pipe.connect(register, 'anat_file_brain', register_gm, 'reference')
    register_pipe.connect(register, 'template_to_anat_file', register_gm, "in_matrix_file")

    # wm
    register_wm = pe.Node(fsl.ApplyXFM(), name = "register_wm")

    register_wm.inputs.in_file = wm_prob_file
    register_wm.inputs.apply_xfm = True
    register_wm.inputs.interp = "nearestneighbour"
    register_wm.inputs.output_type = "NIFTI" # for SPM segment


    register_pipe.connect(register, 'anat_file_brain', register_wm, 'reference')
    register_pipe.connect(register, 'template_to_anat_file', register_wm, "in_matrix_file")


    # csf
    register_csf = pe.Node(fsl.ApplyXFM(), name = "register_csf")

    register_csf.inputs.in_file = csf_prob_file
    register_csf.inputs.apply_xfm = True
    register_csf.inputs.interp = "nearestneighbour"
    register_csf.inputs.output_type = "NIFTI"  # for SPM segment


    register_pipe.connect(register, 'anat_file_brain', register_csf, 'reference')
    register_pipe.connect(register, 'template_to_anat_file', register_csf, "in_matrix_file")


    def return_list(file1, file2 , file3 ):
        return [file1, file2 , file3]

    # merge 3 outputs to a list (...)
    merge_3_files = pe.Node(
        niu.Function(input_names = ["file1","file2","file3"],
                     output_names = ["list3files"],
                     function = return_list),
        name = "merge_3_files")

    register_pipe.connect(register_gm, 'out_file', merge_3_files, "file1")
    register_pipe.connect(register_wm, 'out_file', merge_3_files, "file2")
    register_pipe.connect(register_csf, 'out_file', merge_3_files, "file3")

    ################## same with non linear
    # non linear register between anat and head
    # (FNIRT work directly on head?
    # I thought FLIRT was only skull-stripped brain, is it different? )

    nl_register = pe.Node(fsl.FNIRT(), name = "nl_register")
    nl_register.inputs.in_file = template_file

    register_pipe.connect(inputnode, 'anat_file', nl_register, 'ref_file')
    register_pipe.connect(register, 'template_to_anat_file',
                          nl_register, 'affine_file')

    # apply non linear warp to NMT_SS
    nl_apply = pe.Node(fsl.ApplyWarp(), name="nl_apply")
    nl_apply.inputs.in_file = template_brain_file
    register_pipe.connect(inputnode, 'anat_file', nl_apply, 'ref_file')
    register_pipe.connect(nl_register, 'fieldcoeff_file', nl_apply, 'field_file') ## iout from fnirt

    return register_pipe


def create_register_NMT_pipe(nmt_dir, name = "register_NMT_pipe"):

    """
    Register template to anat with the script NMT_subject_align, and then apply it to tissues list_priors
    ##TODO the wrap of both scripts could be done in a cleaner way with traits
    (one is "done", still one to do)
    """
    register_NMT_pipe = pe.Workflow(name = name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1_file']),
        name='inputnode')

    # N4 intensity normalization over brain
    # maybe not necessary to be in the pipeline?
    # seems to be used only here)

    norm_intensity = pe.Node(ants.N4BiasFieldCorrection(),
                             name='norm_intensity')
    norm_intensity.inputs.dimension = 3
    norm_intensity.inputs.bspline_fitting_distance = 200
    norm_intensity.inputs.n_iterations = [50, 50, 40, 30]
    norm_intensity.inputs.convergence_threshold = 0.00000001
    norm_intensity.inputs.shrink_factor = 2
    norm_intensity.inputs.args = "r 0 --verbose 1"

    register_NMT_pipe.connect(inputnode, 'T1_file',
                               norm_intensity, "input_image")


    # align subj to nmt (with NMT_subject_align, wrapped version with nodes)
    NMT_subject_align = pe.Node(NMTSubjectAlign(), name='NMT_subject_align')

    register_NMT_pipe.connect(norm_intensity, 'output_image',
                              NMT_subject_align, "T1_file")

    NMT_subject_align.inputs.NMT_SS_file = os.path.join(nmt_dir, "NMT_SS.nii.gz")
    NMT_subject_align.inputs.script_file = os.path.join(nmt_dir,"NMT_subject_align.csh")

    # "overwrap" of NwarpApply, with specifying the outputs as wished
    p_dir = os.path.join(nmt_dir, "masks", "probabilisitic_segmentation_masks")

    list_priors = [
        os.path.join(nmt_dir, "NMT.nii.gz"),
        os.path.join(p_dir, "NMT_brainmask_prob.nii.gz"),
        os.path.join(nmt_dir, "masks", "anatomical_masks",
                     "NMT_brainmask.nii.gz"),
        NMT_brainmask_CSF = os.path.join(p_dir, "NMT_segmentation_CSF.nii.gz"),
        NMT_brainmask_GM = os.path.join(p_dir, "NMT_segmentation_GM.nii.gz"),
        NMT_brainmask_WM = os.path.join(p_dir, "NMT_segmentation_WM.nii.gz")]

    align_masks = pe.Node(NwarpApplyPriors(), name='align_masks')
    align_masks.inputs.in_file = list_priors
    align_masks.inputs.out_file = list_priors
    align_masks.inputs.interp = "NN"
    align_masks.inputs.args = "-overwrite"

    register_NMT_pipe.connect(NMT_subject_align, 'shft_aff_file',
                               align_masks, 'master')
    register_NMT_pipe.connect(NMT_subject_align, 'warpinv_file',
                               align_masks, "warp")

    # seg_csf
    align_seg_csf = pe.Node(
        afni.Allineate(), name="align_seg_csf", iterfield=['in_file'])
    align_seg_csf.inputs.final_interpolation = "nearestneighbour"
    align_seg_csf.inputs.overwrite = True
    align_seg_csf.inputs.outputtype = "NIFTI_GZ"

    register_NMT_pipe.connect(align_masks, ('out_file', get_elem, 3),
                               align_seg_csf, "in_file")  # -source
    register_NMT_pipe.connect(norm_intensity, 'output_image',
                               align_seg_csf, "reference")  # -base
    register_NMT_pipe.connect(NMT_subject_align, 'inv_transfo_file',
                               align_seg_csf, "in_matrix")  # -1Dmatrix_apply

    # seg_gm
    align_seg_gm = pe.Node(
        afni.Allineate(), name="align_seg_gm", iterfield=['in_file'])
    align_seg_gm.inputs.final_interpolation = "nearestneighbour"
    align_seg_gm.inputs.overwrite = True
    align_seg_gm.inputs.outputtype = "NIFTI_GZ"

    register_NMT_pipe.connect(align_masks, ('out_file', get_elem, 4),
                               align_seg_gm, "in_file")  # -source
    register_NMT_pipe.connect(norm_intensity, 'output_image',
                               align_seg_gm, "reference")  # -base
    register_NMT_pipe.connect(NMT_subject_align, 'inv_transfo_file',
                               align_seg_gm, "in_matrix")  # -1Dmatrix_apply

    # seg_wm
    align_seg_wm = pe.Node(afni.Allineate(), name="align_seg_wm",
                           iterfield=['in_file'])
    align_seg_wm.inputs.final_interpolation = "nearestneighbour"
    align_seg_wm.inputs.overwrite = True
    align_seg_wm.inputs.outputtype = "NIFTI_GZ"

    register_NMT_pipe.connect(align_masks, ('out_file', get_elem, 5),
                               align_seg_wm, "in_file")  # -source
    register_NMT_pipe.connect(norm_intensity, 'output_image',
                               align_seg_wm, "reference")  # -base
    register_NMT_pipe.connect(NMT_subject_align, 'inv_transfo_file',
                               align_seg_wm, "in_matrix")  # -1Dmatrix_apply

    return register_NMT_pipe
