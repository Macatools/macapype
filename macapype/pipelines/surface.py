import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.spm as spm

from ..nodes.segment import AtroposN4, BinaryFillHoles

from ..utils.misc import get_elem, merge_3_elem_to_list
from ..utils.utils_nodes import NodeParams, parse_key


def create_split_hemi_pipe(template_dir, name="split_hemi_pipe"):

    split_hemi_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['warpinv_file',
                                      'inv_transfo_file',
                                      'shft_aff_file',
                                      't1_ref_file',
                                      'seg_file']),
        name='inputnode')


    # get values
    L_hemi_template_file = "{}/NMT_registration/Haiko89_Asymmetric.Template_n89_brainmask_L.nii.gz".format(template_dir)
    R_hemi_template_file = "{}/NMT_registration/Haiko89_Asymmetric.Template_n89_brainmask_R.nii.gz".format(template_dir)
    cereb_template_file = "{}/NMT_registration/Haiko89_Asymmetric.Template_n89_brainmask_cerebellum.nii.gz".format(template_dir)


    # Warp L hemi template brainmask to subject space
    warp_L_hemi = pe.Node(interface = reg.NwarpApplyPriors(), name='warp_L_hemi')

    warp_L_hemi.inputs.in_file = L_hemi_template_file
    warp_L_hemi.inputs.out_file = L_hemi_template_file
    warp_L_hemi.inputs.interp = "NN"
    warp_L_hemi.inputs.args = "-overwrite"

    split_hemi_pipe.connect(inputnode, 'shft_aff_file', warp_L_hemi, 'master')
    split_hemi_pipe.connect(inputnode, 'warpinv_file', warp_L_hemi, "warp")

    # Align L hemi template
    align_L_hemi = pe.Node(interface = afni.Allineate(), name='align_L_hemi')

    align_L_hemi.inputs.final_interpolation = "nearestneighbour"
    align_L_hemi.inputs.overwrite = True
    align_L_hemi.inputs.outputtype = "NIFTI_GZ"

    split_hemi_pipe.connect(warp_L_hemi, 'out_file',
                              align_L_hemi, "in_file")  # -source
    split_hemi_pipe.connect(inputnode, 't1_ref_file',
                              align_L_hemi, "reference")  # -base
    split_hemi_pipe.connect(inputnode, 'inv_transfo_file',
                              align_L_hemi, "in_matrix")  # -1Dmatrix_apply

    # Warp L hemi template brainmask to subject space
    warp_R_hemi = pe.Node(interface = reg.NwarpApplyPriors(), name='warp_R_hemi')

    warp_R_hemi.inputs.in_file = R_hemi_template_file
    warp_R_hemi.inputs.out_file = R_hemi_template_file
    warp_R_hemi.inputs.interp = "NN"
    warp_R_hemi.inputs.args = "-overwrite"

    split_hemi_pipe.connect(inputnode, 'shft_aff_file', warp_R_hemi, 'master')
    split_hemi_pipe.connect(inputnode, 'warpinv_file', warp_R_hemi, "warp")

    # Align L hemi template
    align_R_hemi = pe.Node(interface = afni.Allineate(), name='align_R_hemi')

    align_R_hemi.inputs.final_interpolation = "nearestneighbour"
    align_R_hemi.inputs.overwrite = True
    align_R_hemi.inputs.outputtype = "NIFTI_GZ"

    split_hemi_pipe.connect(warp_R_hemi, 'out_file',
                              align_R_hemi, "in_file")  # -source
    split_hemi_pipe.connect(inputnode, 't1_ref_file',
                              align_R_hemi, "reference")  # -base
    split_hemi_pipe.connect(inputnode, 'inv_transfo_file',
                              align_R_hemi, "in_matrix")  # -1Dmatrix_apply


    # cereb
    # Binarize cerebellum
    bin_cereb = pe.Node(interface = fsl.UnaryMaths(), name='bin_cereb')
    bin_cereb.inputs.operation = "bin"

    bin_cereb.inputs.in_file = cereb_template_file

    # Warp L hemi template brainmask to subject space
    warp_cereb = pe.Node(interface = reg.NwarpApplyPriors(), name='warp_cereb')

    warp_cereb.inputs.in_file = cereb_template_file
    warp_cereb.inputs.out_file = cereb_template_file
    warp_cereb.inputs.interp = "NN"
    warp_cereb.inputs.args = "-overwrite"


    split_hemi_pipe.connect(bin_cereb, 'out_file', warp_cereb, 'in_file')
    split_hemi_pipe.connect(inputnode, 'shft_aff_file', warp_cereb, 'master')
    split_hemi_pipe.connect(inputnode, 'warpinv_file', warp_cereb, "warp")

    # Align L hemi template
    align_cereb = pe.Node(interface = afni.Allineate(), name='align_cereb')

    align_cereb.inputs.final_interpolation = "nearestneighbour"
    align_cereb.inputs.overwrite = True
    align_cereb.inputs.outputtype = "NIFTI_GZ"

    split_hemi_pipe.connect(warp_cereb, 'out_file',
                              align_cereb, "in_file")  # -source
    split_hemi_pipe.connect(inputnode, 't1_ref_file',
                              align_cereb, "reference")  # -base
    split_hemi_pipe.connect(inputnode, 'inv_transfo_file',
                              align_cereb, "in_matrix")  # -1Dmatrix_apply

    # Using LH and RH masks to obtain left and right hemisphere segmentation masks
    calc_L_hemi = pe.Node(interface = afni.Calc(), name='calc_L_hemi')
    calc_L_hemi.inputs.expr='a*b/b'
    calc_L_hemi.inputs.outputtype ='NIFTI_GZ'

    split_hemi_pipe.connect(inputnode, 'seg_file', calc_L_hemi, "in_file_a")
    split_hemi_pipe.connect(align_L_hemi, 'out_file', calc_L_hemi, "in_file_b")

    calc_R_hemi = pe.Node(interface = afni.Calc(),
                          name='calc_R_hemi')
    calc_R_hemi.inputs.expr='a*b/b'
    calc_R_hemi.inputs.outputtype ='NIFTI_GZ'

    split_hemi_pipe.connect(inputnode, 'seg_file',
                            calc_R_hemi, "in_file_a")
    split_hemi_pipe.connect(align_R_hemi, 'out_file',
                            calc_R_hemi, "in_file_b")


    ##remove cerebellum from left and right brain segmentations
    calc_nocb_L_hemi = pe.Node(interface = afni.Calc(),
                               name='calc_nocb_L_hemi')
    calc_nocb_L_hemi.inputs.expr='(a*(not (b)))'
    calc_nocb_L_hemi.inputs.outputtype ='NIFTI_GZ'

    split_hemi_pipe.connect(calc_L_hemi, 'out_file',
                            calc_nocb_L_hemi, "in_file_a")
    split_hemi_pipe.connect(align_cereb, 'out_file',
                            calc_nocb_L_hemi, "in_file_b")

    calc_nocb_R_hemi = pe.Node(interface = afni.Calc(),
                               name='calc_nocb_R_hemi')
    calc_nocb_R_hemi.inputs.expr='(a*(not (b)))'
    calc_nocb_R_hemi.inputs.outputtype ='NIFTI_GZ'

    split_hemi_pipe.connect(calc_R_hemi, 'out_file',
                            calc_nocb_R_hemi, "in_file_a")
    split_hemi_pipe.connect(align_cereb, 'out_file',
                            calc_nocb_R_hemi, "in_file_b")


    ##create L/R GM and WM no-cerebellum binary masks from subject brain segmentation
    calc_GM_nocb_L_hemi = pe.Node(interface = afni.Calc(),
                                  name='calc_GM_nocb_L_hemi')
    calc_GM_nocb_L_hemi.inputs.expr='iszero(a-2)'
    calc_GM_nocb_L_hemi.inputs.outputtype ='NIFTI_GZ'

    split_hemi_pipe.connect(calc_nocb_L_hemi, 'out_file',
                            calc_GM_nocb_L_hemi, "in_file_a")

    calc_WM_nocb_L_hemi = pe.Node(interface = afni.Calc(),
                                  name='calc_WM_nocb_L_hemi')
    calc_WM_nocb_L_hemi.inputs.expr='iszero(a-3)'
    calc_WM_nocb_L_hemi.inputs.outputtype ='NIFTI_GZ'

    split_hemi_pipe.connect(calc_nocb_L_hemi, 'out_file',
                            calc_WM_nocb_L_hemi, "in_file_a")

    calc_GM_nocb_R_hemi = pe.Node(interface = afni.Calc(),
                                  name='calc_GM_nocb_R_hemi')
    calc_GM_nocb_R_hemi.inputs.expr='iszero(a-2)'
    calc_GM_nocb_R_hemi.inputs.outputtype ='NIFTI_GZ'

    split_hemi_pipe.connect(calc_nocb_R_hemi, 'out_file',
                            calc_GM_nocb_R_hemi, "in_file_a")

    calc_WM_nocb_R_hemi = pe.Node(interface = afni.Calc(),
                                  name='calc_WM_nocb_R_hemi')
    calc_WM_nocb_R_hemi.inputs.expr='iszero(a-3)'
    calc_WM_nocb_R_hemi.inputs.outputtype ='NIFTI_GZ'

    split_hemi_pipe.connect(calc_nocb_R_hemi, 'out_file',
                            calc_WM_nocb_R_hemi, "in_file_a")

    # Extract Cerebellum using template mask transformed to subject space
    extract_cereb = pe.Node(interface = afni.Calc(), name='extract_cereb')
    extract_cereb.inputs.expr='a*b/b'
    extract_cereb.inputs.outputtype ='NIFTI_GZ'

    split_hemi_pipe.connect(inputnode, 't1_ref_file',
                            extract_cereb, "in_file_a")
    split_hemi_pipe.connect(align_cereb, 'out_file',
                            extract_cereb, "in_file_b")

    # Extract L.GM using template mask transformed to subject space
    extract_L_GM = pe.Node(interface = afni.Calc(), name='extract_L_GM')
    extract_L_GM.inputs.expr='a*b/b'
    extract_L_GM.inputs.outputtype ='NIFTI_GZ'

    split_hemi_pipe.connect(inputnode, 't1_ref_file',
                            extract_L_GM, "in_file_a")
    split_hemi_pipe.connect(calc_GM_nocb_L_hemi, 'out_file',
                            extract_L_GM, "in_file_b")

    # Extract L.WM using template mask transformed to subject space
    extract_L_WM = pe.Node(interface = afni.Calc(), name='extract_L_WM')
    extract_L_WM.inputs.expr='a*b/b'
    extract_L_WM.inputs.outputtype ='NIFTI_GZ'

    split_hemi_pipe.connect(inputnode, 't1_ref_file',
                            extract_L_WM, "in_file_a")
    split_hemi_pipe.connect(calc_WM_nocb_L_hemi, 'out_file',
                            extract_L_WM, "in_file_b")

    ##Extract L.GM using template mask transformed to subject space
    extract_R_GM = pe.Node(interface = afni.Calc(), name='extract_R_GM')
    extract_R_GM.inputs.expr='a*b/b'
    extract_R_GM.inputs.outputtype ='NIFTI_GZ'

    split_hemi_pipe.connect(inputnode, 't1_ref_file',
                            extract_R_GM, "in_file_a")
    split_hemi_pipe.connect(calc_GM_nocb_R_hemi, 'out_file',
                            extract_R_GM, "in_file_b")

    ##Extract L.WM using template mask transformed to subject space
    extract_R_WM = pe.Node(interface = afni.Calc(), name='extract_R_WM')
    extract_R_WM.inputs.expr='a*b/b'
    extract_R_WM.inputs.outputtype ='NIFTI_GZ'

    split_hemi_pipe.connect(inputnode, 't1_ref_file',
                            extract_R_WM, "in_file_a")
    split_hemi_pipe.connect(calc_WM_nocb_R_hemi, 'out_file',
                            extract_R_WM, "in_file_b")

    return split_hemi_pipe


def create_surface_pipe(params={}, name="surface_pipe"):
    """
    Description: Segmentation with ANTS atropos script

    Inputs:

        inputnode:
            brain_file: T1 image, after extraction and norm bin_norm_intensity

        arguments:
            params: dictionary of node sub-parameters (from a json file)

            name: pipeline name (default = "segment_atropos_pipe")

    Outputs:

        threshold_csf.out_file:
            csf tissue intensity mask in subject space
        threshold_gm.out_file:
            grey matter tissue intensity mask in subject space
        threshold_wm.out_file:
            white matter tissue intensity mask in subject space
    """
    # creating pipeline
    surface_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['warpinv_file',
                                      'inv_transfo_file',
                                      'shft_aff_file',
                                      't1_ref_file',
                                      'seg_file']),
        name='inputnode')


    if "split_hemi_pipe" in params.keys()

        split_hemi_pipe = create_split_hemi_pipe(
            params = params["split_hemi_pipe"]
            name = "split_hemi_pipe")

    return surface_pipe
