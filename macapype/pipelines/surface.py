
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni

import macapype.nodes.register as reg
from macapype.nodes.surface import Meshify
from macapype.utils.utils_nodes import parse_key, NodeParams


def create_split_hemi_pipe(params, params_template, name="split_hemi_pipe"):

    split_hemi_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['warpinv_file',
                                      'inv_transfo_file',
                                      'shft_aff_file',
                                      't1_ref_file',
                                      'segmented_file']),
        name='inputnode')

    # get values
    L_hemi_template_file = params_template["L_hemi_template"]
    R_hemi_template_file = params_template["R_hemi_template"]
    cereb_template_file = params_template["cereb_template"]

    # Warp L hemi template brainmask to subject space
    warp_L_hemi = pe.Node(interface=reg.NwarpApplyPriors(), name='warp_L_hemi')

    warp_L_hemi.inputs.in_file = L_hemi_template_file
    warp_L_hemi.inputs.out_file = L_hemi_template_file
    warp_L_hemi.inputs.interp = "NN"
    warp_L_hemi.inputs.args = "-overwrite"

    split_hemi_pipe.connect(inputnode, 'shft_aff_file', warp_L_hemi, 'master')
    split_hemi_pipe.connect(inputnode, 'warpinv_file', warp_L_hemi, "warp")

    # Align L hemi template
    align_L_hemi = pe.Node(interface=afni.Allineate(), name='align_L_hemi')

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
    warp_R_hemi = pe.Node(interface=reg.NwarpApplyPriors(), name='warp_R_hemi')

    warp_R_hemi.inputs.in_file = R_hemi_template_file
    warp_R_hemi.inputs.out_file = R_hemi_template_file
    warp_R_hemi.inputs.interp = "NN"
    warp_R_hemi.inputs.args = "-overwrite"

    split_hemi_pipe.connect(inputnode, 'shft_aff_file', warp_R_hemi, 'master')
    split_hemi_pipe.connect(inputnode, 'warpinv_file', warp_R_hemi, "warp")

    # Align L hemi template
    align_R_hemi = pe.Node(interface=afni.Allineate(), name='align_R_hemi')

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
    bin_cereb = pe.Node(interface=fsl.UnaryMaths(), name='bin_cereb')
    bin_cereb.inputs.operation = "bin"

    bin_cereb.inputs.in_file = cereb_template_file

    # Warp L hemi template brainmask to subject space
    warp_cereb = pe.Node(interface=reg.NwarpApplyPriors(), name='warp_cereb')

    warp_cereb.inputs.in_file = cereb_template_file
    warp_cereb.inputs.out_file = cereb_template_file
    warp_cereb.inputs.interp = "NN"
    warp_cereb.inputs.args = "-overwrite"

    split_hemi_pipe.connect(bin_cereb, 'out_file', warp_cereb, 'in_file')
    split_hemi_pipe.connect(inputnode, 'shft_aff_file', warp_cereb, 'master')
    split_hemi_pipe.connect(inputnode, 'warpinv_file', warp_cereb, "warp")

    # Align L hemi template
    align_cereb = pe.Node(interface=afni.Allineate(), name='align_cereb')

    align_cereb.inputs.final_interpolation = "nearestneighbour"
    align_cereb.inputs.overwrite = True
    align_cereb.inputs.outputtype = "NIFTI_GZ"

    split_hemi_pipe.connect(warp_cereb, 'out_file',
                            align_cereb, "in_file")  # -source
    split_hemi_pipe.connect(inputnode, 't1_ref_file',
                            align_cereb, "reference")  # -base
    split_hemi_pipe.connect(inputnode, 'inv_transfo_file',
                            align_cereb, "in_matrix")  # -1Dmatrix_apply

    # Using LH and RH masks to obtain hemisphere segmentation masks
    calc_L_hemi = pe.Node(interface=afni.Calc(), name='calc_L_hemi')
    calc_L_hemi.inputs.expr = 'a*b/b'
    calc_L_hemi.inputs.outputtype = 'NIFTI_GZ'

    split_hemi_pipe.connect(inputnode, 'segmented_file',
                            calc_L_hemi, "in_file_a")
    split_hemi_pipe.connect(align_L_hemi, 'out_file',
                            calc_L_hemi, "in_file_b")

    calc_R_hemi = pe.Node(interface=afni.Calc(),
                          name='calc_R_hemi')
    calc_R_hemi.inputs.expr = 'a*b/b'
    calc_R_hemi.inputs.outputtype = 'NIFTI_GZ'

    split_hemi_pipe.connect(inputnode, 'segmented_file',
                            calc_R_hemi, "in_file_a")
    split_hemi_pipe.connect(align_R_hemi, 'out_file',
                            calc_R_hemi, "in_file_b")

    # remove cerebellum from left and right brain segmentations
    calc_nocb_L_hemi = pe.Node(interface=afni.Calc(),
                               name='calc_nocb_L_hemi')
    calc_nocb_L_hemi.inputs.expr = '(a*(not (b)))'
    calc_nocb_L_hemi.inputs.outputtype = 'NIFTI_GZ'

    split_hemi_pipe.connect(calc_L_hemi, 'out_file',
                            calc_nocb_L_hemi, "in_file_a")
    split_hemi_pipe.connect(align_cereb, 'out_file',
                            calc_nocb_L_hemi, "in_file_b")

    calc_nocb_R_hemi = pe.Node(interface=afni.Calc(),
                               name='calc_nocb_R_hemi')
    calc_nocb_R_hemi.inputs.expr = '(a*(not (b)))'
    calc_nocb_R_hemi.inputs.outputtype = 'NIFTI_GZ'

    split_hemi_pipe.connect(calc_R_hemi, 'out_file',
                            calc_nocb_R_hemi, "in_file_a")
    split_hemi_pipe.connect(align_cereb, 'out_file',
                            calc_nocb_R_hemi, "in_file_b")

    # create L/R GM and WM no-cerebellum masks from subject brain segmentation
    calc_GM_nocb_L_hemi = pe.Node(interface=afni.Calc(),
                                  name='calc_GM_nocb_L_hemi')
    calc_GM_nocb_L_hemi.inputs.expr = 'iszero(a-2)'
    calc_GM_nocb_L_hemi.inputs.outputtype = 'NIFTI_GZ'

    split_hemi_pipe.connect(calc_nocb_L_hemi, 'out_file',
                            calc_GM_nocb_L_hemi, "in_file_a")

    calc_WM_nocb_L_hemi = pe.Node(interface=afni.Calc(),
                                  name='calc_WM_nocb_L_hemi')
    calc_WM_nocb_L_hemi.inputs.expr = 'iszero(a-3)'
    calc_WM_nocb_L_hemi.inputs.outputtype = 'NIFTI_GZ'

    split_hemi_pipe.connect(calc_nocb_L_hemi, 'out_file',
                            calc_WM_nocb_L_hemi, "in_file_a")

    calc_GM_nocb_R_hemi = pe.Node(interface=afni.Calc(),
                                  name='calc_GM_nocb_R_hemi')
    calc_GM_nocb_R_hemi.inputs.expr = 'iszero(a-2)'
    calc_GM_nocb_R_hemi.inputs.outputtype = 'NIFTI_GZ'

    split_hemi_pipe.connect(calc_nocb_R_hemi, 'out_file',
                            calc_GM_nocb_R_hemi, "in_file_a")

    calc_WM_nocb_R_hemi = pe.Node(interface=afni.Calc(),
                                  name='calc_WM_nocb_R_hemi')
    calc_WM_nocb_R_hemi.inputs.expr = 'iszero(a-3)'
    calc_WM_nocb_R_hemi.inputs.outputtype = 'NIFTI_GZ'

    split_hemi_pipe.connect(calc_nocb_R_hemi, 'out_file',
                            calc_WM_nocb_R_hemi, "in_file_a")

    # Extract Cerebellum using template mask transformed to subject space
    extract_cereb = pe.Node(interface=afni.Calc(), name='extract_cereb')
    extract_cereb.inputs.expr = 'a*b/b'
    extract_cereb.inputs.outputtype = 'NIFTI_GZ'

    split_hemi_pipe.connect(inputnode, 't1_ref_file',
                            extract_cereb, "in_file_a")
    split_hemi_pipe.connect(align_cereb, 'out_file',
                            extract_cereb, "in_file_b")

    # Extract L.GM using template mask transformed to subject space
    extract_L_GM = pe.Node(interface=afni.Calc(), name='extract_L_GM')
    extract_L_GM.inputs.expr = 'a*b/b'
    extract_L_GM.inputs.outputtype = 'NIFTI_GZ'

    split_hemi_pipe.connect(inputnode, 't1_ref_file',
                            extract_L_GM, "in_file_a")
    split_hemi_pipe.connect(calc_GM_nocb_L_hemi, 'out_file',
                            extract_L_GM, "in_file_b")

    # Extract L.WM using template mask transformed to subject space
    extract_L_WM = pe.Node(interface=afni.Calc(), name='extract_L_WM')
    extract_L_WM.inputs.expr = 'a*b/b'
    extract_L_WM.inputs.outputtype = 'NIFTI_GZ'

    split_hemi_pipe.connect(inputnode, 't1_ref_file',
                            extract_L_WM, "in_file_a")
    split_hemi_pipe.connect(calc_WM_nocb_L_hemi, 'out_file',
                            extract_L_WM, "in_file_b")

    # Extract L.GM using template mask transformed to subject space
    extract_R_GM = pe.Node(interface=afni.Calc(), name='extract_R_GM')
    extract_R_GM.inputs.expr = 'a*b/b'
    extract_R_GM.inputs.outputtype = 'NIFTI_GZ'

    split_hemi_pipe.connect(inputnode, 't1_ref_file',
                            extract_R_GM, "in_file_a")
    split_hemi_pipe.connect(calc_GM_nocb_R_hemi, 'out_file',
                            extract_R_GM, "in_file_b")

    # Extract L.WM using template mask transformed to subject space
    extract_R_WM = pe.Node(interface=afni.Calc(), name='extract_R_WM')
    extract_R_WM.inputs.expr = 'a*b/b'
    extract_R_WM.inputs.outputtype = 'NIFTI_GZ'

    split_hemi_pipe.connect(inputnode, 't1_ref_file',
                            extract_R_WM, "in_file_a")
    split_hemi_pipe.connect(calc_WM_nocb_R_hemi, 'out_file',
                            extract_R_WM, "in_file_b")

    return split_hemi_pipe


def create_nii_to_mesh_pipe(params, params_template, name="nii_to_mesh_pipe"):

    # creating pipeline
    mesh_to_seg_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['warpinv_file',
                                      'inv_transfo_file',
                                      'shft_aff_file',
                                      't1_ref_file',
                                      'segmented_file']),
        name='inputnode')

    # split hemi pipe (+ cerebellum)
    split_hemi_pipe = create_split_hemi_pipe(
        params=parse_key(params, "split_hemi_pipe"),
        params_template=params_template)

    mesh_to_seg_pipe.connect(inputnode, 'warpinv_file',
                             split_hemi_pipe, 'inputnode.warpinv_file')

    mesh_to_seg_pipe.connect(inputnode, 'shft_aff_file',
                             split_hemi_pipe, 'inputnode.shft_aff_file')

    mesh_to_seg_pipe.connect(inputnode, 'inv_transfo_file',
                             split_hemi_pipe, 'inputnode.inv_transfo_file')

    mesh_to_seg_pipe.connect(inputnode, 't1_ref_file',
                             split_hemi_pipe, 'inputnode.t1_ref_file')

    mesh_to_seg_pipe.connect(inputnode, 'segmented_file',
                             split_hemi_pipe, 'inputnode.segmented_file')

    # meshify L GM hemisphere
    mesh_L_GM = NodeParams(interface=Meshify(),
                           params=parse_key(params, "mesh_L_GM"),
                           name="mesh_L_GM")

    mesh_to_seg_pipe.connect(split_hemi_pipe, 'extract_L_WM.out_file',
                             mesh_L_GM, "image_file")

    # meshify R GM hemisphere
    mesh_R_GM = NodeParams(interface=Meshify(),
                           params=parse_key(params, "mesh_R_GM"),
                           name="mesh_R_GM")

    mesh_to_seg_pipe.connect(split_hemi_pipe, 'extract_R_WM.out_file',
                             mesh_R_GM, "image_file")

    # meshify L WM hemisphere
    mesh_L_WM = NodeParams(interface=Meshify(),
                           params=parse_key(params, "mesh_L_WM"),
                           name="mesh_L_WM")

    mesh_to_seg_pipe.connect(split_hemi_pipe, 'extract_L_WM.out_file',
                             mesh_L_WM, "image_file")

    # meshify R WM hemisphere
    mesh_R_WM = NodeParams(interface=Meshify(),
                           params=parse_key(params, "mesh_R_WM"),
                           name="mesh_R_WM")

    mesh_to_seg_pipe.connect(split_hemi_pipe, 'extract_R_WM.out_file',
                             mesh_R_WM, "image_file")

    return mesh_to_seg_pipe
