
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni
import nipype.interfaces.freesurfer as fs

import macapype.nodes.register as reg
from macapype.nodes.surface import Meshify, split_LR_mask
from macapype.utils.utils_nodes import parse_key, NodeParams


def _create_split_hemi_pipe(params, params_template, name="split_hemi_pipe"):

    """Description: Split segmentated tissus according hemisheres after \
    removal of cortical structure

    Processing steps:

    - TODO

    Params:

        - None so far

    Inputs:

        inputnode:

            warpinv_file:
                non-linear transformation (from NMT_subject_align)

            inv_transfo_file:
                inverse transformation

            aff_file:
                affine transformation file

            t1_ref_file:
                preprocessd T1

            segmented_file:
                from atropos segmentation, with all the tissues segmented

        arguments:

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "split_hemi_pipe")

    Outputs:
    """
    split_hemi_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['warpinv_file',
                                      'inv_transfo_file',
                                      'aff_file',
                                      't1_ref_file',
                                      'segmented_file']),
        name='inputnode')

    # get values

    if "cereb_template" in params_template.keys():
        cereb_template_file = params_template["cereb_template"]

        # ### cereb
        # Binarize cerebellum
        bin_cereb = pe.Node(interface=fsl.UnaryMaths(), name='bin_cereb')
        bin_cereb.inputs.operation = "bin"

        bin_cereb.inputs.in_file = cereb_template_file

        # Warp cereb brainmask to subject space
        warp_cereb = pe.Node(interface=reg.NwarpApplyPriors(),
                             name='warp_cereb')

        warp_cereb.inputs.in_file = cereb_template_file
        warp_cereb.inputs.out_file = cereb_template_file
        warp_cereb.inputs.interp = "NN"
        warp_cereb.inputs.args = "-overwrite"

        split_hemi_pipe.connect(bin_cereb, 'out_file', warp_cereb, 'in_file')
        split_hemi_pipe.connect(inputnode, 'aff_file',
                                warp_cereb, 'master')
        split_hemi_pipe.connect(inputnode, 'warpinv_file', warp_cereb, "warp")

        # Align cereb template
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

    if "L_hemi_template" in params_template.keys() and \
            "R_hemi_template" in params_template.keys():

        L_hemi_template_file = params_template["L_hemi_template"]
        R_hemi_template_file = params_template["R_hemi_template"]

        # Warp L hemi template brainmask to subject space
        warp_L_hemi = pe.Node(interface=reg.NwarpApplyPriors(),
                              name='warp_L_hemi')

        warp_L_hemi.inputs.in_file = L_hemi_template_file
        warp_L_hemi.inputs.out_file = L_hemi_template_file
        warp_L_hemi.inputs.interp = "NN"
        warp_L_hemi.inputs.args = "-overwrite"

        split_hemi_pipe.connect(inputnode, 'aff_file',
                                warp_L_hemi, 'master')
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

        # Warp R hemi template brainmask to subject space
        warp_R_hemi = pe.Node(interface=reg.NwarpApplyPriors(),
                              name='warp_R_hemi')

        warp_R_hemi.inputs.in_file = R_hemi_template_file
        warp_R_hemi.inputs.out_file = R_hemi_template_file
        warp_R_hemi.inputs.interp = "NN"
        warp_R_hemi.inputs.args = "-overwrite"

        split_hemi_pipe.connect(inputnode, 'aff_file',
                                warp_R_hemi, 'master')
        split_hemi_pipe.connect(inputnode, 'warpinv_file', warp_R_hemi, "warp")

        # Align R hemi template
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

    elif "LR_hemi_template" in params_template.keys():

        LR_hemi_template_file = params_template["LR_hemi_template"]

        # Warp LR hemi template brainmask to subject space
        warp_LR_hemi = pe.Node(interface=reg.NwarpApplyPriors(),
                               name='warp_LR_hemi')

        warp_LR_hemi.inputs.in_file = LR_hemi_template_file
        warp_LR_hemi.inputs.out_file = LR_hemi_template_file
        warp_LR_hemi.inputs.interp = "NN"
        warp_LR_hemi.inputs.args = "-overwrite"

        split_hemi_pipe.connect(inputnode, 'aff_file',
                                warp_LR_hemi, 'master')
        split_hemi_pipe.connect(inputnode, 'warpinv_file',
                                warp_LR_hemi, "warp")

        # Align LR hemi template
        align_LR_hemi = pe.Node(interface=afni.Allineate(),
                                name='align_LR_hemi')

        align_LR_hemi.inputs.final_interpolation = "nearestneighbour"
        align_LR_hemi.inputs.overwrite = True
        align_LR_hemi.inputs.outputtype = "NIFTI_GZ"

        split_hemi_pipe.connect(warp_LR_hemi, 'out_file',
                                align_LR_hemi, "in_file")  # -source
        split_hemi_pipe.connect(inputnode, 't1_ref_file',
                                align_LR_hemi, "reference")  # -base
        split_hemi_pipe.connect(inputnode, 'inv_transfo_file',
                                align_LR_hemi, "in_matrix")  # -1Dmatrix_apply

        split_LR = pe.Node(
            interface=niu.Function(
                input_names=["LR_mask_file"],
                output_names=["L_mask_file", "R_mask_file"],
                function=split_LR_mask),
            name="split_LR")

        split_hemi_pipe.connect(align_LR_hemi, "out_file",
                                split_LR, 'LR_mask_file')

    else:
        print("Error, could not find LR_hemi_template or L_hemi_template and \
            R_hemi_template, skipping")
        print(params_template.keys())

        exit()

    # Using LH and RH masks to obtain hemisphere segmentation masks
    calc_L_hemi = pe.Node(interface=afni.Calc(), name='calc_L_hemi')
    calc_L_hemi.inputs.expr = 'a*b/b'
    calc_L_hemi.inputs.outputtype = 'NIFTI_GZ'

    split_hemi_pipe.connect(inputnode, 'segmented_file',
                            calc_L_hemi, "in_file_a")

    if "LR_hemi_template" in params_template.keys():
        split_hemi_pipe.connect(split_LR, 'L_mask_file',
                                calc_L_hemi, "in_file_b")
    else:
        split_hemi_pipe.connect(align_L_hemi, 'out_file',
                                calc_L_hemi, "in_file_b")

    # R_hemi
    calc_R_hemi = pe.Node(interface=afni.Calc(),
                          name='calc_R_hemi')
    calc_R_hemi.inputs.expr = 'a*b/b'
    calc_R_hemi.inputs.outputtype = 'NIFTI_GZ'

    split_hemi_pipe.connect(inputnode, 'segmented_file',
                            calc_R_hemi, "in_file_a")

    if "LR_hemi_template" in params_template.keys():

        split_hemi_pipe.connect(split_LR, 'R_mask_file',
                                calc_R_hemi, "in_file_b")
    else:
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
    """
    Description: basic nii to mesh pipeline after segmentation

    Processing steps:

    - split in hemisphere after removal of the subcortical structures
    - using scipy marching cube methods to compute mesh
    - some smoothing (using brain-slam)

    Params:

        - split_hemi_pipe (see :class:`_create_split_hemi_pipe \
        <macapype.pipelines.surface._create_split_hemi_pipe>` for arguments)
        - mesh_L_GM, mesh_R_GM, mesh_L_WM, mesh_R_WM (see :class:`Meshify  \
        <macapype.nodes.surface.Meshify>` for arguments)

    Inputs:

        inputnode:

            warpinv_file:
                non-linear transformation (from NMT_subject_align)

            inv_transfo_file:
                inverse transformation

            aff_file:
                affine transformation file

            t1_ref_file:
                preprocessd T1

            segmented_file:
                from atropos segmentation, with all the tissues segmented

        arguments:

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "nii_to_mesh_pipe")

    Outputs:
    """
    # creating pipeline
    mesh_to_seg_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['warpinv_file',
                                      'inv_transfo_file',
                                      'aff_file',
                                      't1_ref_file',
                                      'segmented_file']),
        name='inputnode')

    # split hemi pipe (+ cerebellum)
    split_hemi_pipe = _create_split_hemi_pipe(
        params=parse_key(params, "split_hemi_pipe"),
        params_template=params_template)

    mesh_to_seg_pipe.connect(inputnode, 'warpinv_file',
                             split_hemi_pipe, 'inputnode.warpinv_file')

    mesh_to_seg_pipe.connect(inputnode, 'inv_transfo_file',
                             split_hemi_pipe, 'inputnode.inv_transfo_file')

    mesh_to_seg_pipe.connect(inputnode, 'aff_file',
                             split_hemi_pipe, 'inputnode.aff_file')

    mesh_to_seg_pipe.connect(inputnode, 't1_ref_file',
                             split_hemi_pipe, 'inputnode.t1_ref_file')

    mesh_to_seg_pipe.connect(inputnode, 'segmented_file',
                             split_hemi_pipe, 'inputnode.segmented_file')

    # meshify L GM hemisphere
    mesh_L_GM = NodeParams(interface=Meshify(),
                           params=parse_key(params, "mesh_L_GM"),
                           name="mesh_L_GM")

    mesh_to_seg_pipe.connect(split_hemi_pipe, 'extract_L_GM.out_file',
                             mesh_L_GM, "image_file")

    # meshify R GM hemisphere
    mesh_R_GM = NodeParams(interface=Meshify(),
                           params=parse_key(params, "mesh_R_GM"),
                           name="mesh_R_GM")

    mesh_to_seg_pipe.connect(split_hemi_pipe, 'extract_R_GM.out_file',
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


###############################################################################
# using freesurfer tools to build the mesh through tesselation
def create_nii_to_mesh_fs_pipe(params, name="nii_to_mesh_fs_pipe"):

    """
    Description: surface generation using freesurfer tools

    Params:

    - fill_wm (see `MRIFill <https://nipype.readthedocs.io/en/0.12.1/\
    interfaces/generated/nipype.interfaces.freesurfer.utils.html#mrifill>`_) \
    - also available as :ref:`indiv_params <indiv_params>`


    Inputs:

        inputnode:

            wm_mask_file:
                segmented white matter mask (binary) in template space

            reg_brain_file:
                preprocessd T1, registered to template

            indiv_params (opt):
                dict with individuals parameters for some nodes

        arguments:

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "nii_to_mesh_fs_pipe")

    Outputs:

    """
    # creating pipeline
    nii_to_mesh_fs_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['wm_mask_file', 'reg_brain_file',
                                      'indiv_params']),
        name='inputnode')

    # bin_wm
    bin_wm = pe.Node(interface=fsl.UnaryMaths(), name="bin_wm")
    bin_wm.inputs.operation = "fillh"

    nii_to_mesh_fs_pipe.connect(inputnode, 'wm_mask_file',
                                bin_wm, 'in_file')

    # resample everything
    refit_wm = pe.Node(interface=afni.Refit(), name="refit_wm")
    refit_wm.inputs.args = "-xdel 1.0 -ydel 1.0 -zdel 1.0 -keepcen"

    nii_to_mesh_fs_pipe.connect(bin_wm, 'out_file',
                                refit_wm, 'in_file')

    # resample everything
    refit_reg = pe.Node(interface=afni.Refit(), name="refit_reg")
    refit_reg.inputs.args = "-xdel 1.0 -ydel 1.0 -zdel 1.0 -keepcen"

    nii_to_mesh_fs_pipe.connect(inputnode, 'reg_brain_file',
                                refit_reg, 'in_file')

    # mri_convert wm to freesurfer mgz
    convert_wm = pe.Node(interface=fs.MRIConvert(),
                         name="convert_wm")
    convert_wm.inputs.out_type = "mgz"
    convert_wm.inputs.conform = True

    nii_to_mesh_fs_pipe.connect(refit_wm, 'out_file',
                                convert_wm, 'in_file')

    # mri_convert reg to freesurfer mgz
    convert_reg = pe.Node(interface=fs.MRIConvert(),
                          name="convert_reg")
    convert_reg.inputs.out_type = "mgz"
    convert_reg.inputs.conform = True

    nii_to_mesh_fs_pipe.connect(refit_reg, 'out_file',
                                convert_reg, 'in_file')

    # mri_fill
    fill_wm = NodeParams(interface=fs.MRIFill(),
                         params=parse_key(params, "fill_wm"),
                         name="fill_wm")

    fill_wm.inputs.out_file = "filled.mgz"

    nii_to_mesh_fs_pipe.connect(convert_wm, 'out_file',
                                fill_wm, 'in_file')

    nii_to_mesh_fs_pipe.connect(
        inputnode, ("indiv_params", parse_key, "fill_wm"),
        fill_wm, 'indiv_params')

    # pretesselate wm
    pretess_wm = pe.Node(interface=fs.MRIPretess(),
                         name="pretess_wm")
    pretess_wm.inputs.label = 255

    nii_to_mesh_fs_pipe.connect(fill_wm, 'out_file',
                                pretess_wm, 'in_filled')

    nii_to_mesh_fs_pipe.connect(convert_reg, 'out_file',
                                pretess_wm, 'in_norm')

    # tesselate wm lh
    tess_wm_lh = pe.Node(interface=fs.MRITessellate(), name="tess_wm_lh")
    tess_wm_lh.inputs.label_value = 255
    tess_wm_lh.inputs.out_file = "lh_tess"

    nii_to_mesh_fs_pipe.connect(pretess_wm, 'out_file',
                                tess_wm_lh, 'in_file')

    # tesselate wm rh
    tess_wm_rh = pe.Node(interface=fs.MRITessellate(), name="tess_wm_rh")
    tess_wm_rh.inputs.label_value = 127
    tess_wm_rh.inputs.out_file = "rh_tess"

    nii_to_mesh_fs_pipe.connect(pretess_wm, 'out_file',
                                tess_wm_rh, 'in_file')

    # ExtractMainComponent lh
    extract_mc_lh = pe.Node(interface=fs.ExtractMainComponent(),
                            name="extract_mc_lh")

    nii_to_mesh_fs_pipe.connect(tess_wm_lh, 'surface',
                                extract_mc_lh, 'in_file')

    extract_mc_lh.inputs.out_file = "lh.lh_tess.maincmp"

    # ExtractMainComponent rh
    extract_mc_rh = pe.Node(interface=fs.ExtractMainComponent(),
                            name="extract_mc_rh")

    nii_to_mesh_fs_pipe.connect(tess_wm_rh, 'surface',
                                extract_mc_rh, 'in_file')

    extract_mc_rh.inputs.out_file = "rh.rh_tess.maincmp"

    # SmoothTessellation lh
    smooth_tess_lh = pe.Node(interface=fs.SmoothTessellation(),
                             name="smooth_tess_lh")
    smooth_tess_lh.inputs.disable_estimates = True

    nii_to_mesh_fs_pipe.connect(extract_mc_lh, 'out_file',
                                smooth_tess_lh, 'in_file')

    # SmoothTessellation rh
    smooth_tess_rh = pe.Node(interface=fs.SmoothTessellation(),
                             name="smooth_tess_rh")
    smooth_tess_rh.inputs.disable_estimates = True

    nii_to_mesh_fs_pipe.connect(extract_mc_rh, 'out_file',
                                smooth_tess_rh, 'in_file')

    return nii_to_mesh_fs_pipe
