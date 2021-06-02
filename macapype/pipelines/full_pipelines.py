
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from nipype.interfaces import fsl

from ..utils.utils_nodes import NodeParams

from macapype.nodes.correct_bias import T1xT2BiasFieldCorrection
from macapype.nodes.register import IterREGBET

from .prepare import (create_short_preparation_pipe,
                      create_short_preparation_FLAIR_pipe,
                      create_short_preparation_MD_pipe,
                      create_short_preparation_T1_pipe,
                      create_long_multi_preparation_pipe,
                      create_long_single_preparation_pipe)

from .segment import (create_old_segment_pipe,
                      create_native_old_segment_pipe,
                      create_segment_atropos_pipe,
                      create_segment_atropos_seg_pipe,
                      create_mask_from_seg_pipe)

from .correct_bias import (create_masked_correct_bias_pipe,
                           create_correct_bias_pipe)

from .register import create_register_NMT_pipe, create_native_iter_reg_pipe

from .extract_brain import (create_extract_pipe,
                            create_extract_T1_pipe)

from .surface import create_nii_to_mesh_pipe, create_nii_to_mesh_fs_pipe

from macapype.utils.misc import parse_key, list_input_files


###############################################################################
# SPM based segmentation (from: Régis Trapeau)
# -soft SPM or SPM_T1
###############################################################################
def create_full_spm_subpipes(
        params_template, params={}, name='full_spm_subpipes'):
    """ Description: SPM based segmentation pipeline from T1w and T2w images
    in template space

    Processing steps:

    - Data preparation (short, with betcrop or crop)
    - debias using T1xT2BiasFieldCorrection (using mask is betcrop)
    - registration to template file with IterREGBET
    - SPM segmentation the old way (SPM8, not dartel based)

    Params:

    - short_data_preparation_pipe (see :class:`create_short_preparation_pipe \
    <macapype.pipelines.prepare.create_short_preparation_pipe>`)
    - debias (see :class:`T1xT2BiasFieldCorrection \
    <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>`) - also available \
    as :ref:`indiv_params <indiv_params>`
    - reg (see :class:`IterREGBET <macapype.nodes.register.IterREGBET>`) - \
    also available as :ref:`indiv_params <indiv_params>`
    - old_segment_pipe (see :class:`create_old_segment_pipe \
    <macapype.pipelines.segment.create_old_segment_pipe>`)
    - nii_to_mesh_fs_pipe (see :class:`create_nii_to_mesh_fs_pipe \
    <macapype.pipelines.surface.create_nii_to_mesh_fs_pipe>`)

    Inputs:

        inputnode:

            list_T1:
                T1 file names

            list_T2:
                T2 file names

            indiv_params (opt):
                dict with individuals parameters for some nodes


        arguments:

            params_template:
                dict of template files containing brain_template and priors \
            (list of template based segmented tissues)

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "full_spm_subpipes")

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
        niu.IdentityInterface(fields=['list_T1', 'list_T2', 'indiv_params']),
        name='inputnode'
    )

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['brain_mask', 'norm_T1',
                                      'segmented_brain_mask']),
        name='outputnode')

    # preprocessing
    if 'short_preparation_pipe' in params.keys():

        data_preparation_pipe = create_short_preparation_pipe(
            params=parse_key(params, "short_preparation_pipe"))
    else:
        print("Error, short_preparation_pipe was not \
            found in params, skipping")
        return seg_pipe

    seg_pipe.connect(inputnode, 'list_T1',
                     data_preparation_pipe, 'inputnode.list_T1')
    seg_pipe.connect(inputnode, 'list_T2',
                     data_preparation_pipe, 'inputnode.list_T2')
    seg_pipe.connect(inputnode, 'indiv_params',
                     data_preparation_pipe, 'inputnode.indiv_params')

    # Bias correction of cropped images
    debias = NodeParams(T1xT2BiasFieldCorrection(),
                        params=parse_key(params, "debias"),
                        name='debias')

    seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                     debias, 't1_file')
    seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T2',
                     debias, 't2_file')
    seg_pipe.connect(inputnode, ('indiv_params', parse_key, "debias"),
                     debias, 'indiv_params')

    if 'bet_crop' in parse_key(params, "short_preparation_pipe"):
        seg_pipe.connect(data_preparation_pipe, 'bet_crop.mask_file',
                         debias, 'b')
    else:
        debias.inputs.bet = 1

    seg_pipe.connect(debias, 'debiased_mask_file',
                     outputnode, 'brain_mask')

    # Iterative registration to the INIA19 template
    reg = NodeParams(IterREGBET(),
                     params=parse_key(params, "reg"),
                     name='reg')

    reg.inputs.refb_file = params_template["template_brain"]

    seg_pipe.connect(debias, 't1_debiased_file', reg, 'inw_file')
    seg_pipe.connect(debias, 't1_debiased_brain_file',
                     reg, 'inb_file')

    seg_pipe.connect(inputnode, ('indiv_params', parse_key, "reg"),
                     reg, 'indiv_params')

    seg_pipe.connect(reg, 'warp_file',
                     outputnode, 'norm_T1')

    # Compute brain mask using old_segment of SPM and postprocessing on
    # tissues' masks
    if "old_segment_pipe" in params.keys():

        old_segment_pipe = create_old_segment_pipe(
            params_template, params=parse_key(params, "old_segment_pipe"))

        seg_pipe.connect(reg, 'warp_file',
                         old_segment_pipe, 'inputnode.T1')

        seg_pipe.connect(
            inputnode, 'indiv_params',
            old_segment_pipe, 'inputnode.indiv_params')

    else:
        return seg_pipe

    # not mandatory
    if "nii_to_mesh_fs_pipe" in params.keys():
        nii_to_mesh_fs_pipe = create_nii_to_mesh_fs_pipe(
            params=parse_key(params, "nii_to_mesh_fs_pipe"))

        seg_pipe.connect(reg, 'warp_file',
                         nii_to_mesh_fs_pipe, 'inputnode.reg_brain_file')

        seg_pipe.connect(old_segment_pipe, 'outputnode.threshold_wm',
                         nii_to_mesh_fs_pipe, 'inputnode.wm_mask_file')

        seg_pipe.connect(inputnode, 'indiv_params',
                         nii_to_mesh_fs_pipe, 'inputnode.indiv_params')

    # not mandatory
    if "mask_from_seg_pipe" in params.keys():
        mask_from_seg_pipe = create_mask_from_seg_pipe(
            params=parse_key(params, "mask_from_seg_pipe"))

        seg_pipe.connect(old_segment_pipe, 'outputnode.threshold_csf',
                         mask_from_seg_pipe, 'inputnode.mask_csf')

        seg_pipe.connect(old_segment_pipe, 'outputnode.threshold_wm',
                         mask_from_seg_pipe, 'inputnode.mask_wm')

        seg_pipe.connect(old_segment_pipe, 'outputnode.threshold_gm',
                         mask_from_seg_pipe, 'inputnode.mask_gm')

        seg_pipe.connect(inputnode, 'indiv_params',
                         mask_from_seg_pipe, 'inputnode.indiv_params')

        seg_pipe.connect(mask_from_seg_pipe, 'merge_indexed_mask.indexed_mask',
                         outputnode, 'segmented_brain_mask')

    return seg_pipe


###############################################################################
# SPM based segmentation (from: Régis Trapeau)
# -soft SPM_native or SPM_T1_native
###############################################################################
def create_full_native_spm_subpipes(
        params_template, params={}, name='full_native_spm_subpipes'):
    """ Description: SPM based segmentation pipeline from T1w and T2w images
    in template space

    Processing steps:

    - Data preparation (short, with betcrop or crop)
    - debias using T1xT2BiasFieldCorrection (using mask is betcrop)
    - registration to template file with IterREGBET
    - SPM segmentation the old way (SPM8, not dartel based)

    Params:

    - short_data_preparation_pipe (see :class:`create_short_preparation_pipe \
    <macapype.pipelines.prepare.create_short_preparation_pipe>`)
    - debias (see :class:`T1xT2BiasFieldCorrection \
    <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>`) - also available \
    as :ref:`indiv_params <indiv_params>`
    - reg (see :class:`IterREGBET <macapype.nodes.register.IterREGBET>`) - \
    also available as :ref:`indiv_params <indiv_params>`
    - native_old_segment_pipe (see :class:`create_native_old_segment_pipe \
    <macapype.pipelines.segment.create_old_segment_pipe>`)

    Inputs:

        inputnode:

            list_T1:
                T1 file names

            list_T2:
                T2 file names

            indiv_params (opt):
                dict with individuals parameters for some nodes


        arguments:

            params_template:
                dict of template files containing brain_template and priors \
            (list of template based segmented tissues)

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "full_spm_subpipes")

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
        niu.IdentityInterface(fields=['list_T1', 'list_T2', 'indiv_params']),
        name='inputnode'
    )

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['brain_mask', 'segmented_brain_mask']),
        name='outputnode')

    # preprocessing
    if 'short_preparation_pipe' in params.keys():

        data_preparation_pipe = create_short_preparation_pipe(
            params=parse_key(params, "short_preparation_pipe"))
    else:
        print("Error, short_preparation_pipe was not \
            found in params, skipping")
        return seg_pipe

    seg_pipe.connect(inputnode, 'list_T1',
                     data_preparation_pipe, 'inputnode.list_T1')
    seg_pipe.connect(inputnode, 'list_T2',
                     data_preparation_pipe, 'inputnode.list_T2')
    seg_pipe.connect(inputnode, 'indiv_params',
                     data_preparation_pipe, 'inputnode.indiv_params')

    # Bias correction of cropped images
    debias = NodeParams(T1xT2BiasFieldCorrection(),
                        params=parse_key(params, "debias"),
                        name='debias')

    seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                     debias, 't1_file')
    seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T2',
                     debias, 't2_file')
    seg_pipe.connect(inputnode, ('indiv_params', parse_key, "debias"),
                     debias, 'indiv_params')

    if 'bet_crop' in parse_key(params, "short_preparation_pipe"):
        seg_pipe.connect(data_preparation_pipe, 'bet_crop.mask_file',
                         debias, 'b')
    else:
        debias.inputs.bet = 1

    seg_pipe.connect(debias, 'debiased_mask_file',
                     outputnode, 'brain_mask')

    if "native_iter_reg_pipe" in params.keys():
        native_reg_pipe = create_native_iter_reg_pipe(
            params_template,
            params=parse_key(params, "native_iter_reg_pipe"))

        seg_pipe.connect(debias, 't1_debiased_brain_file',
                         native_reg_pipe, 'inputnode.t1_debiased_brain_file')

        seg_pipe.connect(debias, 't1_debiased_file',
                         native_reg_pipe, 'inputnode.t1_debiased_file')

        seg_pipe.connect(inputnode, 'indiv_params',
                         native_reg_pipe, 'inputnode.indiv_params')
    else:
        return seg_pipe

    # Compute brain mask using old_segment of SPM and postprocessing on
    # tissues' masks
    if "native_old_segment_pipe" in params.keys():

        native_old_segment_pipe = create_native_old_segment_pipe(
            params_template,
            params=parse_key(params, "native_old_segment_pipe"))

        seg_pipe.connect(debias, 't1_debiased_file',
                         native_old_segment_pipe, 'inputnode.T1')

        seg_pipe.connect(native_reg_pipe, 'register_csf_to_nat.out_file',
                         native_old_segment_pipe, 'inputnode.native_csf')

        seg_pipe.connect(native_reg_pipe, 'register_wm_to_nat.out_file',
                         native_old_segment_pipe, 'inputnode.native_wm')

        seg_pipe.connect(native_reg_pipe, 'register_gm_to_nat.out_file',
                         native_old_segment_pipe, 'inputnode.native_gm')

        seg_pipe.connect(inputnode, 'indiv_params',
                         native_old_segment_pipe, 'inputnode.indiv_params')

    else:
        return seg_pipe

    if "mask_from_seg_pipe" in params.keys():
        mask_from_seg_pipe = create_mask_from_seg_pipe(
            params=parse_key(params, "mask_from_seg_pipe"))

        seg_pipe.connect(native_old_segment_pipe, 'outputnode.threshold_csf',
                         mask_from_seg_pipe, 'inputnode.mask_csf')

        seg_pipe.connect(native_old_segment_pipe, 'outputnode.threshold_wm',
                         mask_from_seg_pipe, 'inputnode.mask_wm')

        seg_pipe.connect(native_old_segment_pipe, 'outputnode.threshold_gm',
                         mask_from_seg_pipe, 'inputnode.mask_gm')

        seg_pipe.connect(inputnode, 'indiv_params',
                         mask_from_seg_pipe, 'inputnode.indiv_params')

        seg_pipe.connect(mask_from_seg_pipe, 'merge_indexed_mask.indexed_mask',
                         outputnode, 'segmented_brain_mask')

    return seg_pipe


###############################################################################
# FLAIR after SPM based segmentation
# -soft SPM_FLAIR or SPM_T1_FLAIR
###############################################################################
def create_transfo_FLAIR_pipe(params_template, params={},
                              name='transfo_FLAIR_pipe'):
    """ Description: apply tranformation to FLAIR, MD and FA if necssary

    Processing steps:

    - -coreg FA on T1
    - apply coreg on MD
    - debias using T1xT2BiasFieldCorrection (using mask is betcrop)
    - registration to template file with IterREGBET
    - SPM segmentation the old way (SPM8, not dartel based)

    Params:

    - short_data_preparation_pipe (see :class:`create_short_preparation_pipe \
    <macapype.pipelines.prepare.create_short_preparation_pipe>`)
    - debias (see :class:`T1xT2BiasFieldCorrection \
    <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>`) - also available \
    as :ref:`indiv_params <indiv_params>`
    - reg (see :class:`IterREGBET <macapype.nodes.register.IterREGBET>`) - \
    also available as :ref:`indiv_params <indiv_params>`
    - old_segment_pipe (see :class:`create_old_segment_pipe \
    <macapype.pipelines.segment.create_old_segment_pipe>`)
    - nii_to_mesh_fs_pipe (see :class:`create_nii_to_mesh_fs_pipe \
    <macapype.pipelines.surface.create_nii_to_mesh_fs_pipe>`)

    Inputs:

        inputnode:

            SS_T1:
                T1 file names

            orig_T1:
                T2 file names

            FLAIR:
                flair file name

            transfo_file:
                Transformation file between native to template

            inv_transfo_file:
                Transformation file between template and native

            threshold_wm:
                gm binary tissue in template space

            indiv_params (opt):
                dict with individuals parameters for some nodes

        outputnode:

            coreg_FLAIR:
                FLAIR coregistered to T1

            norm_FLAIR:
                FLAIR normalised in template space

        arguments:

            params_template:
                dict of template files containing brain_template and priors \
            (list of template based segmented tissues)

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "full_spm_subpipes")

    Outputs:

    """

    print("Transfo FLAIR pipe name: ", name)

    # Creating pipeline
    transfo_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['orig_T1', 'FLAIR', 'lin_transfo_file']),
        name='inputnode'
    )

    data_preparation_pipe = create_short_preparation_FLAIR_pipe(
        params=parse_key(params, "short_preparation_pipe"))

    transfo_pipe.connect(inputnode, 'orig_T1',
                         data_preparation_pipe, 'inputnode.orig_T1')
    transfo_pipe.connect(inputnode, 'FLAIR',
                         data_preparation_pipe, 'inputnode.FLAIR')

    # apply norm to FLAIR
    norm_lin_FLAIR = pe.Node(fsl.ApplyXFM(), name="norm_lin_FLAIR")
    norm_lin_FLAIR.inputs.reference = params_template["template_brain"]

    transfo_pipe.connect(data_preparation_pipe, 'outputnode.coreg_FLAIR',
                         norm_lin_FLAIR, 'in_file')
    transfo_pipe.connect(inputnode, 'lin_transfo_file',
                         norm_lin_FLAIR, 'in_matrix_file')

    # Creating output node
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=['coreg_FLAIR', 'norm_FLAIR']),
        name='outputnode'
    )

    transfo_pipe.connect(data_preparation_pipe, 'outputnode.coreg_FLAIR',
                         outputnode, 'coreg_FLAIR')

    transfo_pipe.connect(norm_lin_FLAIR, 'out_file',
                         outputnode, 'norm_FLAIR')

    return transfo_pipe


# SPM with MD
def create_transfo_MD_pipe(params_template, params={},
                           name='transfo_MD_pipe'):
    """ Description: apply tranformation to FLAIR, MD and FA if necssary

    Processing steps:

    - -coreg FA on T1
    - apply coreg on MD
    - debias using T1xT2BiasFieldCorrection (using mask is betcrop)
    - registration to template file with IterREGBET
    - SPM segmentation the old way (SPM8, not dartel based)

    Params:

    - short_data_preparation_pipe (see :class:`create_short_preparation_pipe \
    <macapype.pipelines.prepare.create_short_preparation_pipe>`)
    - debias (see :class:`T1xT2BiasFieldCorrection \
    <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>`) - also available \
    as :ref:`indiv_params <indiv_params>`
    - reg (see :class:`IterREGBET <macapype.nodes.register.IterREGBET>`) - \
    also available as :ref:`indiv_params <indiv_params>`
    - old_segment_pipe (see :class:`create_old_segment_pipe \
    <macapype.pipelines.segment.create_old_segment_pipe>`)
    - nii_to_mesh_fs_pipe (see :class:`create_nii_to_mesh_fs_pipe \
    <macapype.pipelines.surface.create_nii_to_mesh_fs_pipe>`)

    Inputs:

        inputnode:

            SS_T1:
                T1 file names

            orig_T1:
                T2 file names

            FLAIR:
                flair file name

            transfo_file:
                Transformation file between native to template

            inv_transfo_file:
                Transformation file between template and native

            threshold_wm:
                gm binary tissue in template space

            indiv_params (opt):
                dict with individuals parameters for some nodes


        arguments:

            params_template:
                dict of template files containing brain_template and priors \
            (list of template based segmented tissues)

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "full_spm_subpipes")

    Outputs:

    """

    print("Transfo MD pipe name: ", name)

    # Creating pipeline
    transfo_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['SS_T1', 'orig_T1', 'MD', 'b0mean',
                    'threshold_wm', 'lin_transfo_file',
                    'inv_lin_transfo_file']),
        name='inputnode'
    )

    compute_native_wm = pe.Node(fsl.ApplyXFM(), name='compute_native_wm')

    transfo_pipe.connect(inputnode, 'threshold_wm',
                         compute_native_wm, 'in_file')

    transfo_pipe.connect(inputnode, 'orig_T1',
                         compute_native_wm, 'reference')

    transfo_pipe.connect(inputnode, 'inv_lin_transfo_file',
                         compute_native_wm, 'in_matrix_file')

    data_preparation_pipe = create_short_preparation_MD_pipe(
        params=parse_key(params, "short_preparation_pipe"))

    transfo_pipe.connect(inputnode, 'orig_T1',
                         data_preparation_pipe, 'inputnode.orig_T1')
    transfo_pipe.connect(inputnode, 'SS_T1',
                         data_preparation_pipe, 'inputnode.SS_T1')
    transfo_pipe.connect(inputnode, 'MD',
                         data_preparation_pipe, 'inputnode.MD')
    transfo_pipe.connect(inputnode, 'b0mean',
                         data_preparation_pipe, 'inputnode.b0mean')
    transfo_pipe.connect(compute_native_wm, 'out_file',
                         data_preparation_pipe, 'inputnode.native_wm_mask')

    # apply norm to coreg_MD
    norm_lin_MD = pe.Node(fsl.ApplyXFM(), name="norm_lin_MD")
    norm_lin_MD.inputs.reference = params_template["template_brain"]

    transfo_pipe.connect(data_preparation_pipe, 'outputnode.coreg_MD',
                         norm_lin_MD, 'in_file')
    transfo_pipe.connect(inputnode, 'lin_transfo_file',
                         norm_lin_MD, 'in_matrix_file')

    # apply norm to coreg_better_MD
    norm_lin_better_MD = pe.Node(fsl.ApplyXFM(), name="norm_lin_better_MD")
    norm_lin_better_MD.inputs.reference = params_template["template_brain"]

    transfo_pipe.connect(data_preparation_pipe, 'outputnode.coreg_better_MD',
                         norm_lin_better_MD, 'in_file')
    transfo_pipe.connect(inputnode, 'lin_transfo_file',
                         norm_lin_better_MD, 'in_matrix_file')

    return transfo_pipe


###############################################################################
# ANTS based segmentation (from Kepkee Loh / Julien Sein)
# (-soft ANTS)
###############################################################################
def create_brain_extraction_pipe(params_template, params={},
                                 name="brain_extraction_pipe"):
    """ Description: Brain extraction with atlas-brex after debiasing

    Params:

    - correct_bias_pipe (see :class:`create_correct_bias_pipe \
    <macapype.pipelines.correct_bias.create_correct_bias_pipe>`)
    - extract_pipe (see `create_extract_pipe <macapype.pipeline.\
    extract_brain.create_extract_pipe>`)


    Inputs:

        inputnode:

            preproc_T1:
                preprocessed T1 file

            preproc_T2:
                preprocessed T2 file

            indiv_params (opt):
                dict with individuals parameters for some nodes


        arguments:

            params_template:
                dictionary of template files

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "full_segment_pipe")

    Outputs:

    """
    # creating pipeline
    brain_extraction_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['preproc_T1', 'preproc_T2',
                                      'indiv_params']),
        name='inputnode')

    # Correct_bias_T1_T2
    correct_bias_pipe = create_correct_bias_pipe(
        params=parse_key(params, "correct_bias_pipe"))

    brain_extraction_pipe.connect(inputnode, 'preproc_T1',
                                  correct_bias_pipe, 'inputnode.preproc_T1')
    brain_extraction_pipe.connect(inputnode, 'preproc_T2',
                                  correct_bias_pipe, 'inputnode.preproc_T2')

    # brain extraction
    extract_pipe = create_extract_pipe(
        params_template=params_template,
        params=parse_key(params, "extract_pipe"))

    brain_extraction_pipe.connect(correct_bias_pipe, "outputnode.debiased_T1",
                                  extract_pipe, "inputnode.restore_T1")
    brain_extraction_pipe.connect(correct_bias_pipe, "outputnode.debiased_T2",
                                  extract_pipe, "inputnode.restore_T2")
    brain_extraction_pipe.connect(inputnode, "indiv_params",
                                  extract_pipe, "inputnode.indiv_params")
    return brain_extraction_pipe


def create_brain_segment_from_mask_pipe(
        params_template, params={}, name="brain_segment_from_mask_pipe",
        NMT_version="v1.3"):
    """ Description: Segment T1 (using T2 for bias correction) and a previously
    computed mask with NMT Atlas and atropos segment.

    Params:

    - masked_correct_bias_pipe (see :class:`create_masked_correct_bias_pipe \
    <macapype.pipelines.correct_bias.create_masked_correct_bias_pipe>`)
    - register_NMT_pipe (see :class:`create_register_NMT_pipe \
    <macapype.pipelines.register.create_register_NMT_pipe>`)
    - segment_atropos_pipe (see :class:`create_segment_atropos_pipe \
    <macapype.pipelines.segment.create_segment_atropos_pipe>`)

    Inputs:

        inputnode:

            preproc_T1:
                preprocessed T1 file name

            preproc_T2:
                preprocessed T2 file name

            brain_mask:
                a mask computed for the same T1/T2 images

            indiv_params (opt):
                dict with individuals parameters for some nodes


        arguments:

            params_template:
                dictionary of template files

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "full_segment_pipe")

    Outputs:

    """
    # creating pipeline
    brain_segment_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['preproc_T1', 'preproc_T2', 'brain_mask', 'indiv_params']),
        name='inputnode')

    # correcting for bias T1/T2, but this time with a mask
    masked_correct_bias_pipe = create_masked_correct_bias_pipe(
        params=parse_key(params, "masked_correct_bias_pipe"))

    brain_segment_pipe.connect(
        inputnode, 'preproc_T1',
        masked_correct_bias_pipe, "inputnode.preproc_T1")
    brain_segment_pipe.connect(
        inputnode, 'preproc_T2',
        masked_correct_bias_pipe, "inputnode.preproc_T2")
    brain_segment_pipe.connect(
        inputnode, 'brain_mask',
        masked_correct_bias_pipe, "inputnode.brain_mask")

    # register NMT template, template mask and priors to subject T1
    register_NMT_pipe = create_register_NMT_pipe(
        params_template=params_template,
        params=parse_key(params, "register_NMT_pipe"), NMT_version=NMT_version)

    brain_segment_pipe.connect(
        masked_correct_bias_pipe, 'outputnode.mask_debiased_T1',
        register_NMT_pipe, "inputnode.T1")
    brain_segment_pipe.connect(
        inputnode, 'indiv_params',
        register_NMT_pipe, "inputnode.indiv_params")

    # ants Atropos

    if NMT_version == "v2.0":

        segment_atropos_pipe = create_segment_atropos_seg_pipe(
            params=parse_key(params, "segment_atropos_pipe"))

        brain_segment_pipe.connect(
            register_NMT_pipe, 'align_seg.out_file', segment_atropos_pipe,
            "inputnode.seg_file")
    else:
        segment_atropos_pipe = create_segment_atropos_pipe(
            params=parse_key(params, "segment_atropos_pipe"))

        brain_segment_pipe.connect(
            register_NMT_pipe, 'align_seg_csf.out_file', segment_atropos_pipe,
            "inputnode.csf_prior_file")
        brain_segment_pipe.connect(
            register_NMT_pipe, 'align_seg_gm.out_file', segment_atropos_pipe,
            "inputnode.gm_prior_file")
        brain_segment_pipe.connect(
            register_NMT_pipe, 'align_seg_wm.out_file', segment_atropos_pipe,
            "inputnode.wm_prior_file")

    brain_segment_pipe.connect(
        register_NMT_pipe, 'norm_intensity.output_image',
        segment_atropos_pipe, "inputnode.brain_file")

    return brain_segment_pipe


def create_full_ants_subpipes(
        params_template, params={}, name="full_ants_subpipes", mask_file=None):
    """Description: Segment T1 (using T2 for bias correction) .

    Params:

    - short_data_preparation_pipe (see :class:`create_short_preparation_pipe \
    <macapype.pipelines.prepare.create_short_preparation_pipe>`) or \
    long_single_preparation_pipe \
    (see :class:`create_long_single_preparation_pipe \
    <macapype.pipelines.prepare.create_long_single_preparation_pipe>`) or \
    long_multi_preparation_pipe \
    (see :class:`create_long_multi_preparation_pipe \
    <macapype.pipelines.prepare.create_long_multi_preparation_pipe>`)

    - brain_extraction_pipe (see :class:`create_brain_extraction_pipe \
    <macapype.pipelines.full_pipelines.create_brain_extraction_pipe>`)
    - brain_segment_pipe (see :class:`create_brain_segment_from_mask_pipe\
    <macapype.pipelines.full_pipelines.create_brain_segment_from_mask_pipe>`)
    - nii_to_mesh_pipe (see :class:`create_nii_to_mesh_pipe\
    <macapype.pipelines.surface.create_nii_to_mesh_pipe>`)

    Inputs:

        inputnode:

            list_T1:
                preprocessed T1 file name

            list_T2:
                preprocessed T2 file name

            indiv_params (opt):
                dict with individuals parameters for some nodes

        arguments:

            params_template:
                dictionary of template files

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "full_segment_pipe")

    Outputs:

        brain_mask

        segmented_brain_mask:
            indexed with tissue classes

    """

    # creating pipeline
    seg_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['list_T1', 'list_T2', 'indiv_params']),
        name='inputnode'
    )

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['brain_mask', 'segmented_brain_mask']),
        name='outputnode')

    # preprocessing
    if 'long_single_preparation_pipe' in params.keys():
        data_preparation_pipe = create_long_single_preparation_pipe(
            params=parse_key(params, "long_single_preparation_pipe"))

    elif 'long_multi_preparation_pipe' in params.keys():
        data_preparation_pipe = create_long_multi_preparation_pipe(
            params=parse_key(params, "long_multi_preparation_pipe"))

    elif 'short_preparation_pipe' in params.keys():
        data_preparation_pipe = create_short_preparation_pipe(
            params=parse_key(params, "short_preparation_pipe"))

    else:
        print("Error, short_preparation_pipe, long_single_preparation_pipe or\
            long_multi_preparation_pipe was not found in params, skipping")

        test_node = pe.Node(niu.Function(input_names=['list_T1', 'list_T2'],
                                         output_names=[''],
                                         function=list_input_files),
                            name="test_node")

        seg_pipe.connect(inputnode, 'list_T1',
                         test_node, 'list_T1')
        seg_pipe.connect(inputnode, 'list_T2',
                         test_node, 'list_T2')

        return seg_pipe

    seg_pipe.connect(inputnode, 'list_T1',
                     data_preparation_pipe, 'inputnode.list_T1')
    seg_pipe.connect(inputnode, 'list_T2',
                     data_preparation_pipe, 'inputnode.list_T2')
    seg_pipe.connect(inputnode, 'indiv_params',
                     data_preparation_pipe, 'inputnode.indiv_params')

    if mask_file is None:

        # full extract brain pipeline (correct_bias, denoising, extract brain)
        if "brain_extraction_pipe" not in params.keys():
            return seg_pipe

        brain_extraction_pipe = create_brain_extraction_pipe(
            params=parse_key(params, "brain_extraction_pipe"),
            params_template=params_template)

        seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                         brain_extraction_pipe, 'inputnode.preproc_T1')
        seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T2',
                         brain_extraction_pipe, 'inputnode.preproc_T2')

        seg_pipe.connect(inputnode, 'indiv_params',
                         brain_extraction_pipe, 'inputnode.indiv_params')

    # full_segment (restarting from the avg_align files)
    if "brain_segment_pipe" not in params.keys():
        return seg_pipe

    if params["general"]["template_name"].split("_")[0] == "NMT":
        print("found NMT template")
        NMT_version = params["general"]["template_name"].split("_")[1]
    else:
        print("Not NMT template, NMT version used by default for processing")
        NMT_version = "v1.3"

    print("NMT_version:", NMT_version)

    brain_segment_pipe = create_brain_segment_from_mask_pipe(
        params_template=params_template,
        params=parse_key(params, "brain_segment_pipe"),
        NMT_version=NMT_version)

    seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                     brain_segment_pipe, 'inputnode.preproc_T1')
    seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T2',
                     brain_segment_pipe, 'inputnode.preproc_T2')

    if mask_file is None:

        seg_pipe.connect(brain_extraction_pipe,
                         "extract_pipe.smooth_mask.out_file",
                         brain_segment_pipe, "inputnode.brain_mask")

        seg_pipe.connect(brain_extraction_pipe,
                         "extract_pipe.smooth_mask.out_file",
                         outputnode, "brain_mask")

    else:
        # TODO this is weird
        brain_segment_pipe.inputs.inputnode.brain_mask = mask_file

        seg_pipe.inputs.outputnode.brain_mask = mask_file

    seg_pipe.connect(inputnode, 'indiv_params',
                     brain_segment_pipe, 'inputnode.indiv_params')

    if "mask_from_seg_pipe" in params.keys():
        mask_from_seg_pipe = create_mask_from_seg_pipe(
            params=parse_key(params, "mask_from_seg_pipe"))

        seg_pipe.connect(brain_segment_pipe,
                         'segment_atropos_pipe.outputnode.threshold_csf',
                         mask_from_seg_pipe, 'inputnode.mask_csf')

        seg_pipe.connect(brain_segment_pipe,
                         'segment_atropos_pipe.outputnode.threshold_wm',
                         mask_from_seg_pipe, 'inputnode.mask_wm')

        seg_pipe.connect(brain_segment_pipe,
                         'segment_atropos_pipe.outputnode.threshold_gm',
                         mask_from_seg_pipe, 'inputnode.mask_gm')

        seg_pipe.connect(inputnode, 'indiv_params',
                         mask_from_seg_pipe, 'inputnode.indiv_params')

        seg_pipe.connect(mask_from_seg_pipe, 'merge_indexed_mask.indexed_mask',
                         outputnode, 'segmented_brain_mask')

    if 'nii_to_mesh_pipe' in params.keys():

        nii_to_mesh_pipe = create_nii_to_mesh_pipe(
            params_template=params_template,
            params=parse_key(params, "nii_to_mesh_pipe"))

        # from data_preparation_pipe
        seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                         nii_to_mesh_pipe, 'inputnode.t1_ref_file')

        # from brain_segment_pipe
        seg_pipe.connect(brain_segment_pipe,
                         'register_NMT_pipe.NMT_subject_align.warpinv_file',
                         nii_to_mesh_pipe, 'inputnode.warpinv_file')

        seg_pipe.connect(
            brain_segment_pipe,
            'register_NMT_pipe.NMT_subject_align.inv_transfo_file',
            nii_to_mesh_pipe, 'inputnode.inv_transfo_file')

        seg_pipe.connect(brain_segment_pipe,
                         'register_NMT_pipe.NMT_subject_align.aff_file',
                         nii_to_mesh_pipe, 'inputnode.aff_file')

        seg_pipe.connect(brain_segment_pipe,
                         'segment_atropos_pipe.outputnode.segmented_file',
                         nii_to_mesh_pipe, "inputnode.segmented_file")

    elif "nii_to_mesh_fs_pipe" in params.keys():
        nii_to_mesh_fs_pipe = create_nii_to_mesh_fs_pipe(
            params=parse_key(params, "nii_to_mesh_fs_pipe"))

        seg_pipe.connect(brain_extraction_pipe,
                         'correct_bias_pipe.outputnode.debiased_T1',
                         nii_to_mesh_fs_pipe, 'inputnode.reg_brain_file')

        seg_pipe.connect(brain_segment_pipe,
                         'segment_atropos_pipe.outputnode.threshold_wm',
                         nii_to_mesh_fs_pipe, 'inputnode.wm_mask_file')

        seg_pipe.connect(inputnode, 'indiv_params',
                         nii_to_mesh_fs_pipe, 'inputnode.indiv_params')

    return seg_pipe


###############################################################################
# ANTS based segmentation for adrien baboons (T1 without T2)
# -soft ANTS_T1
###############################################################################
# same as above, but replacing biascorrection with N4biascorrection
# in brain extraction and brain segmentation
def create_brain_extraction_T1_pipe(params_template, params={},
                                    name="brain_extraction_T1_pipe"):
    """
    Description: Brain extraction with only T1 images.

    - extract_T1_pipe (see `create_extract_T1_pipe <macapype.pipeline.\
    extract_brain.create_extract_T1_pipe>`)

    Inputs:

        inputnode:

            preproc_T1:
                preprocessed T1 file

            indiv_params (opt):
                dict with individuals parameters for some nodes

        arguments:

            params_template:
                dictionary of template files

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "full_segment_pipe")

    Outputs:

    """

    # creating pipeline
    brain_extraction_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['preproc_T1', 'indiv_params']),
        name='inputnode')

    # brain extraction (with atlasbrex)
    extract_T1_pipe = create_extract_T1_pipe(
        params_template=params_template,
        params=parse_key(params, "extract_T1_pipe"))

    brain_extraction_pipe.connect(inputnode, "preproc_T1",
                                  extract_T1_pipe, "inputnode.restore_T1")
    brain_extraction_pipe.connect(inputnode, "indiv_params",
                                  extract_T1_pipe, "inputnode.indiv_params")
    return brain_extraction_pipe


def create_brain_segment_from_mask_T1_pipe(
        params_template, params={}, name="brain_segment_from_mask_T1_pipe"):
    """
    Description: Segment T1 from a previously computed mask.

    Params:

    - register_NMT_pipe (see :class:`create_register_NMT_pipe \
    <macapype.pipelines.register.create_register_NMT_pipe>`)
    - segment_atropos_pipe (see :class:`create_segment_atropos_pipe \
    <macapype.pipelines.segment.create_segment_atropos_pipe>`)

    Inputs:

        inputnode:

            preproc_T1:
                preprocessed T1 file name

            brain_mask:
                a mask computed for the same T1/T2 images

            indiv_params (opt):
                dict with individuals parameters for some nodes


        arguments:

            params_template:
                dictionary of template files

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "full_segment_pipe")

    Outputs:

    """
    # creating pipeline
    brain_segment_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['preproc_T1', 'brain_mask', 'indiv_params']),
        name='inputnode')

    # mask T1 using brain mask and perform N4 bias correction

    # restore_mask_T1
    restore_mask_T1 = pe.Node(fsl.ApplyMask(), name='restore_mask_T1')

    brain_segment_pipe.connect(inputnode, 'preproc_T1',
                               restore_mask_T1, 'in_file')
    brain_segment_pipe.connect(inputnode, 'brain_mask',
                               restore_mask_T1, 'mask_file')

    NMT_version = "v1.3"

    print("NMT_version:", NMT_version)

    # register NMT template, template mask and priors to subject T1
    register_NMT_pipe = create_register_NMT_pipe(
        params_template=params_template,
        params=parse_key(params, "register_NMT_pipe"), NMT_version=NMT_version)

    brain_segment_pipe.connect(
        restore_mask_T1, 'out_file',
        register_NMT_pipe, "inputnode.T1")
    brain_segment_pipe.connect(
        inputnode, 'indiv_params',
        register_NMT_pipe, "inputnode.indiv_params")

    # ants Atropos
    segment_atropos_pipe = create_segment_atropos_pipe(
        params=parse_key(params, "segment_atropos_pipe"))

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


def create_full_T1_ants_subpipes(params_template, params={},
                                 name="full_T1_ants_subpipes"):
    """Description: Full pipeline to segment T1 (with no T2).

    Params:

    - short_data_preparation_pipe (see :class:`create_short_preparation_pipe <\
    macapype.pipelines.prepare.create_short_preparation_pipe>`
    - brain_extraction_T1_pipe (see :class:`create_brain_extraction_T1_pipe \
    <macapype.pipelines.full_pipelines.create_brain_extraction_T1_pipe>`)
    - brain_segment_T1_pipe (see \
    :class:`create_brain_segment_from_mask_T1_pipe \
<macapype.pipelines.full_pipelines.create_brain_segment_from_mask_T1_pipe>`)

    Inputs:

        inputnode:

            list_T1:
                preprocessed T1 file name

            indiv_params (opt):
                dict with individuals parameters for some nodes

        arguments:

            params_template:
                dictionary of template files

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "full_segment_pipe")

    Outputs:

    """

    # creating pipeline
    seg_pipe = pe.Workflow(name=name)

    # Creating input node (grab only T1 files)
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['list_T1', 'indiv_params']),
        name='inputnode'
    )

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['brain_mask', 'segmented_brain_mask']),
        name='outputnode')

    # preprocessing (perform preparation pipe with only T1)
    if 'short_preparation_T1_pipe' in params.keys():
        data_preparation_pipe = create_short_preparation_T1_pipe(
            params=parse_key(params, "short_preparation_T1_pipe"))

    else:
        print("Error, short_preparation_T1_pipe was not found in params, \
            skipping")
        return seg_pipe

    seg_pipe.connect(inputnode, 'list_T1',
                     data_preparation_pipe, 'inputnode.list_T1')
    seg_pipe.connect(inputnode, 'indiv_params',
                     data_preparation_pipe, 'inputnode.indiv_params')

    # full extract brain pipeline (correct_bias, denoising, extract brain)
    if "brain_extraction_T1_pipe" not in params.keys():
        return seg_pipe

    brain_extraction_pipe = create_brain_extraction_T1_pipe(
        params=parse_key(params, "brain_extraction_T1_pipe"),
        params_template=params_template)

    seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                     brain_extraction_pipe, 'inputnode.preproc_T1')
    seg_pipe.connect(inputnode, 'indiv_params',
                     brain_extraction_pipe, 'inputnode.indiv_params')

    seg_pipe.connect(brain_extraction_pipe,
                     "extract_T1_pipe.smooth_mask.out_file",
                     outputnode, "brain_mask")

    # full_segment (restarting from the avg_align files)
    if "brain_segment_T1_pipe" not in params.keys():
        return seg_pipe

    brain_segment_pipe = create_brain_segment_from_mask_T1_pipe(
        params_template=params_template,
        params=parse_key(params, "brain_segment_T1_pipe"))

    seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                     brain_segment_pipe, 'inputnode.preproc_T1')
    seg_pipe.connect(brain_extraction_pipe,
                     "extract_T1_pipe.smooth_mask.out_file",
                     brain_segment_pipe, "inputnode.brain_mask")
    seg_pipe.connect(inputnode, 'indiv_params',
                     brain_segment_pipe, 'inputnode.indiv_params')

    if "mask_from_seg_pipe" in params.keys():
        mask_from_seg_pipe = create_mask_from_seg_pipe(
            params=parse_key(params, "mask_from_seg_pipe"))

        seg_pipe.connect(brain_segment_pipe,
                         'segment_atropos_pipe.outputnode.threshold_csf',
                         mask_from_seg_pipe, 'inputnode.mask_csf')

        seg_pipe.connect(brain_segment_pipe,
                         'segment_atropos_pipe.outputnode.threshold_wm',
                         mask_from_seg_pipe, 'inputnode.mask_wm')

        seg_pipe.connect(brain_segment_pipe,
                         'segment_atropos_pipe.outputnode.threshold_gm',
                         mask_from_seg_pipe, 'inputnode.mask_gm')

        seg_pipe.connect(inputnode, 'indiv_params',
                         mask_from_seg_pipe, 'inputnode.indiv_params')

        seg_pipe.connect(mask_from_seg_pipe, 'merge_indexed_mask.indexed_mask',
                         outputnode, 'segmented_brain_mask')

    if "nii_to_mesh_fs_pipe" in params.keys():
        nii_to_mesh_fs_pipe = create_nii_to_mesh_fs_pipe(
            params=parse_key(params, "nii_to_mesh_fs_pipe"))

        seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                         nii_to_mesh_fs_pipe, 'inputnode.reg_brain_file')

        seg_pipe.connect(brain_segment_pipe,
                         'segment_atropos_pipe.outputnode.threshold_wm',
                         nii_to_mesh_fs_pipe, 'inputnode.wm_mask_file')

        seg_pipe.connect(inputnode, 'indiv_params',
                         nii_to_mesh_fs_pipe, 'inputnode.indiv_params')

    return seg_pipe
