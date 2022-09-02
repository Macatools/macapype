"""
    Gather all full pipelines

"""
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from nipype.interfaces import fsl
from nipype.interfaces import ants

from nipype.interfaces.niftyreg import regutils

from ..utils.utils_nodes import NodeParams

from macapype.nodes.correct_bias import T1xT2BiasFieldCorrection
from macapype.nodes.register import IterREGBET
from macapype.nodes.prepare import padding_cropped_img

from .prepare import (create_short_preparation_pipe,
                      create_short_preparation_FLAIR_pipe,
                      create_short_preparation_MD_pipe,
                      create_short_preparation_T1_pipe,
                      create_long_multi_preparation_pipe,
                      create_long_single_preparation_pipe,)

from .segment import (create_old_segment_pipe,
                      create_native_old_segment_pipe,
                      create_segment_atropos_pipe,
                      create_segment_atropos_seg_pipe,
                      create_mask_from_seg_pipe,
                      create_5tt_pipe)

from .correct_bias import (create_masked_correct_bias_pipe,
                           create_correct_bias_pipe)

from .register import (create_register_NMT_pipe, create_reg_seg_pipe)

from .extract_brain import (create_extract_pipe,
                            create_extract_T1_pipe)

from .surface import create_nii_to_mesh_pipe, create_nii_to_mesh_fs_pipe

from macapype.utils.misc import parse_key, list_input_files, show_files


###############################################################################
# SPM based segmentation (from: Régis Trapeau)
# -soft SPM or SPM_T1
###############################################################################
def create_full_spm_subpipes(
        params_template, params_template_aladin,
        params={}, name='full_spm_subpipes',
        pad=False, space='template'):

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
        niu.IdentityInterface(fields=['brain_mask', 'segmented_brain_mask',
                                      'debiased_T1', 'debiased_brain',
                                      'prob_wm', 'prob_gm', 'prob_csf']),
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
            params=parse_key(params, "short_preparation_pipe"),
            params_template=params_template_aladin)

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

    if pad:
        if "short_preparation_pipe" in params.keys():
            if "crop_T1" in params["short_preparation_pipe"].keys():

                print("Padding mask in native space")
                pad_mask = pe.Node(
                    niu.Function(
                        input_names=['cropped_img_file', 'orig_img_file',
                                     'indiv_crop'],
                        output_names=['padded_img_file'],
                        function=padding_cropped_img),
                    name="pad_mask")

                seg_pipe.connect(debias, 'debiased_mask_file',
                                 pad_mask, "cropped_img_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_mask, "orig_img_file")

                seg_pipe.connect(inputnode, "indiv_params",
                                 pad_mask, "indiv_crop")

                seg_pipe.connect(pad_mask, "padded_img_file",
                                 outputnode, "brain_mask")

                print("Padding debiased_T1 in native space")
                pad_debiased_T1 = pe.Node(
                    niu.Function(
                        input_names=['cropped_img_file', 'orig_img_file',
                                     'indiv_crop'],
                        output_names=['padded_img_file'],
                        function=padding_cropped_img),
                    name="pad_debiased_T1")

                seg_pipe.connect(debias, 't1_debiased_file',
                                 pad_debiased_T1, "cropped_img_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_debiased_T1, "orig_img_file")

                seg_pipe.connect(inputnode, "indiv_params",
                                 pad_debiased_T1, "indiv_crop")

                seg_pipe.connect(pad_debiased_T1, "padded_img_file",
                                 outputnode, "debiased_T1")

                print("Padding debiased_brain in native space")
                pad_debiased_brain = pe.Node(
                    niu.Function(
                        input_names=['cropped_img_file', 'orig_img_file',
                                     'indiv_crop'],
                        output_names=['padded_img_file'],
                        function=padding_cropped_img),
                    name="pad_debiased_brain")

                seg_pipe.connect(debias, 't1_debiased_brain_file',
                                 pad_debiased_brain, "cropped_img_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_debiased_brain, "orig_img_file")

                seg_pipe.connect(inputnode, "indiv_params",
                                 pad_debiased_brain, "indiv_crop")

                seg_pipe.connect(pad_debiased_brain, "padded_img_file",
                                 outputnode, "debiased_brain")

            else:
                print("Using reg_aladin transfo to pad mask back")
                pad_mask = pe.Node(regutils.RegResample(), name="pad_mask")

                seg_pipe.connect(debias, "debiased_mask_file",
                                 pad_mask, "flo_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_mask, "ref_file")

                seg_pipe.connect(data_preparation_pipe, "inv_tranfo.out_file",
                                 pad_mask, "trans_file")

                print("Using reg_aladin transfo to pad debiased_brain back")
                pad_debiased_brain = pe.Node(regutils.RegResample(),
                                             name="pad_debiased_brain")

                seg_pipe.connect(debias, 't1_debiased_brain_file',
                                 pad_debiased_brain, "flo_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_debiased_brain, "ref_file")

                seg_pipe.connect(data_preparation_pipe, "inv_tranfo.out_file",
                                 pad_debiased_brain, "trans_file")

                print("Using reg_aladin transfo to pad debiased_T1 back")
                pad_debiased_T1 = pe.Node(regutils.RegResample(),
                                          name="pad_debiased_T1")

                seg_pipe.connect(debias, 't1_debiased_file',
                                 pad_debiased_T1, "flo_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_debiased_T1, "ref_file")

                seg_pipe.connect(data_preparation_pipe, "inv_tranfo.out_file",
                                 pad_debiased_T1, "trans_file")

                # outputnode
                seg_pipe.connect(pad_mask, "out_file",
                                 outputnode, "brain_mask")

                seg_pipe.connect(pad_debiased_brain, "out_file",
                                 outputnode, "debiased_brain")

                seg_pipe.connect(pad_debiased_T1, "out_file",
                                 outputnode, "debiased_T1")

    else:
        seg_pipe.connect(debias, "debiased_mask_file",
                         outputnode, "brain_mask")

        seg_pipe.connect(debias, 't1_debiased_brain_file',
                         outputnode, "debiased_brain")

        seg_pipe.connect(debias, 't1_debiased_file',
                         outputnode, "debiased_T1")

    # Iterative registration to the INIA19 template
    reg = NodeParams(IterREGBET(),
                     params=parse_key(params, "reg"),
                     name='reg')

    reg.inputs.refb_file = params_template["template_brain"]

    seg_pipe.connect(debias, 't1_debiased_file',
                     reg, 'inw_file')

    seg_pipe.connect(debias, 't1_debiased_brain_file',
                     reg, 'inb_file')

    seg_pipe.connect(inputnode, ('indiv_params', parse_key, "reg"),
                     reg, 'indiv_params')

    # Compute brain mask using old_segment of SPM and postprocessing on
    # tissues' masks
    if "old_segment_pipe" not in params.keys():
        print("No segmentation, skipping")
        return seg_pipe

    if space == "template":

        old_segment_pipe = create_old_segment_pipe(
            params_template, params=parse_key(params, "old_segment_pipe"))

        seg_pipe.connect(reg, 'warp_file',
                         old_segment_pipe, 'inputnode.T1')

        seg_pipe.connect(inputnode, 'indiv_params',
                         old_segment_pipe, 'inputnode.indiv_params')

    elif space == "native":

        old_segment_pipe = create_native_old_segment_pipe(
            params_template, params=parse_key(params, "old_segment_pipe"))

        seg_pipe.connect(reg, 'warp_file',
                         old_segment_pipe, 'inputnode.T1')

        seg_pipe.connect(reg, 'inv_transfo_file',
                         old_segment_pipe, 'inputnode.inv_transfo_file')

        seg_pipe.connect(debias, 't1_debiased_brain_file',
                         old_segment_pipe, 'inputnode.native_T1')

        seg_pipe.connect(inputnode, 'indiv_params',
                         old_segment_pipe, 'inputnode.indiv_params')
    else:

        print("Error, space={}".format(space))
        return seg_pipe

    # prob_wm
    if pad and space == "native":
        if "short_preparation_pipe" in params.keys():
            if "crop_T1" in params["short_preparation_pipe"].keys():

                print("Padding prob_wm in native space")

                pad_prob_wm = pe.Node(
                    niu.Function(
                        input_names=['cropped_img_file', 'orig_img_file',
                                     'indiv_crop'],
                        output_names=['padded_img_file'],
                        function=padding_cropped_img),
                    name="pad_prob_wm")

                seg_pipe.connect(old_segment_pipe, "outputnode.prob_wm",
                                 pad_prob_wm, "cropped_img_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_prob_wm, "orig_img_file")

                seg_pipe.connect(inputnode, "indiv_params",
                                 pad_prob_wm, "indiv_crop")

                seg_pipe.connect(pad_prob_wm, "padded_img_file",
                                 outputnode, "prob_wm")

            elif "bet_crop" in params["short_preparation_pipe"].keys():
                print("Not implemented yet")

            else:
                print("Using reg_aladin transfo to pad prob_wm back")

                pad_prob_wm = pe.Node(regutils.RegResample(),
                                      name="pad_prob_wm")

                seg_pipe.connect(old_segment_pipe, "outputnode.prob_wm",
                                 pad_prob_wm, "flo_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_prob_wm, "ref_file")

                seg_pipe.connect(data_preparation_pipe, "inv_tranfo.out_file",
                                 pad_prob_wm, "trans_file")

                # outputnode
                seg_pipe.connect(pad_prob_wm, "out_file",
                                 outputnode, "prob_wm")

    else:
        seg_pipe.connect(old_segment_pipe, 'outputnode.prob_wm',
                         outputnode, 'prob_wm')

    # prob_csf
    if pad and space == "native":
        if "short_preparation_pipe" in params.keys():
            if "crop_T1" in params["short_preparation_pipe"].keys():

                print("Padding prob_csf in native space")

                pad_prob_csf = pe.Node(
                    niu.Function(
                        input_names=['cropped_img_file', 'orig_img_file',
                                     'indiv_crop'],
                        output_names=['padded_img_file'],
                        function=padding_cropped_img),
                    name="pad_prob_csf")

                seg_pipe.connect(old_segment_pipe, "outputnode.prob_csf",
                                 pad_prob_csf, "cropped_img_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_prob_csf, "orig_img_file")

                seg_pipe.connect(inputnode, "indiv_params",
                                 pad_prob_csf, "indiv_crop")

                seg_pipe.connect(pad_prob_csf, "padded_img_file",
                                 outputnode, "prob_csf")

            elif "bet_crop" in params["short_preparation_pipe"].keys():
                print("Not implemented yet")

            else:
                print("Using reg_aladin transfo to pad prob_csf back")

                pad_prob_csf = pe.Node(regutils.RegResample(),
                                       name="pad_prob_csf")

                seg_pipe.connect(old_segment_pipe, "outputnode.prob_csf",
                                 pad_prob_csf, "flo_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_prob_csf, "ref_file")

                seg_pipe.connect(data_preparation_pipe, "inv_tranfo.out_file",
                                 pad_prob_csf, "trans_file")

                # outputnode
                seg_pipe.connect(pad_prob_csf, "out_file",
                                 outputnode, "prob_csf")

    else:
        seg_pipe.connect(old_segment_pipe, 'outputnode.prob_csf',
                         outputnode, 'prob_csf')

    # prob_gm
    if pad and space == "native":
        if "short_preparation_pipe" in params.keys():
            if "crop_T1" in params["short_preparation_pipe"].keys():

                print("Padding prob_gm in native space")

                pad_prob_gm = pe.Node(
                    niu.Function(
                        input_names=['cropped_img_file', 'orig_img_file',
                                     'indiv_crop'],
                        output_names=['padded_img_file'],
                        function=padding_cropped_img),
                    name="pad_prob_gm")

                seg_pipe.connect(old_segment_pipe, "outputnode.prob_gm",
                                 pad_prob_gm, "cropped_img_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_prob_gm, "orig_img_file")

                seg_pipe.connect(inputnode, "indiv_params",
                                 pad_prob_gm, "indiv_crop")

                seg_pipe.connect(pad_prob_gm, "padded_img_file",
                                 outputnode, "prob_gm")

            elif "bet_crop" in params["short_preparation_pipe"].keys():
                print("Not implemented yet")

            else:
                print("Using reg_aladin transfo to pad prob_gm back")

                pad_prob_gm = pe.Node(regutils.RegResample(),
                                      name="pad_prob_gm")

                seg_pipe.connect(old_segment_pipe, "outputnode.prob_gm",
                                 pad_prob_gm, "flo_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_prob_gm, "ref_file")

                seg_pipe.connect(data_preparation_pipe, "inv_tranfo.out_file",
                                 pad_prob_gm, "trans_file")

                # outputnode
                seg_pipe.connect(pad_prob_gm, "out_file",
                                 outputnode, "prob_gm")

    else:
        seg_pipe.connect(old_segment_pipe, 'outputnode.prob_gm',
                         outputnode, 'prob_gm')

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

        # seg_mask
        if pad and space == "native":
            if "short_preparation_pipe" in params.keys():
                if "crop_T1" in params["short_preparation_pipe"].keys():

                    print("Padding seg_mask in native space")

                    pad_seg_mask = pe.Node(
                        niu.Function(
                            input_names=['cropped_img_file', 'orig_img_file',
                                         'indiv_crop'],
                            output_names=['padded_img_file'],
                            function=padding_cropped_img),
                        name="pad_seg_mask")

                    seg_pipe.connect(mask_from_seg_pipe,
                                     'merge_indexed_mask.indexed_mask',
                                     pad_seg_mask, "cropped_img_file")

                    seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                     pad_seg_mask, "orig_img_file")

                    seg_pipe.connect(inputnode, "indiv_params",
                                     pad_seg_mask, "indiv_crop")

                    seg_pipe.connect(pad_seg_mask, "padded_img_file",
                                     outputnode, "segmented_brain_mask")

                elif "bet_crop" in params["short_preparation_pipe"].keys():
                    print("Not implemented yet")

                else:
                    print("Using reg_aladin transfo to pad seg_mask back")

                    pad_seg_mask = pe.Node(regutils.RegResample(),
                                           name="pad_seg_mask")

                    seg_pipe.connect(mask_from_seg_pipe,
                                     'merge_indexed_mask.indexed_mask',
                                     pad_seg_mask, "flo_file")

                    seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                     pad_seg_mask, "ref_file")

                    seg_pipe.connect(data_preparation_pipe,
                                     "inv_tranfo.out_file",
                                     pad_seg_mask, "trans_file")

                    # outputnode
                    seg_pipe.connect(pad_seg_mask, "out_file",
                                     outputnode, "segmented_brain_mask")

        else:
            seg_pipe.connect(mask_from_seg_pipe,
                             'merge_indexed_mask.indexed_mask',
                             outputnode, 'segmented_brain_mask')

    if space == 'template':

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
        params=parse_key(params, "short_preparation_FLAIR_pipe"))

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
            fields=['orig_T1', 'SS_T2', 'MD', 'b0mean',
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
        params=parse_key(params, "short_preparation_MD_pipe"))

    transfo_pipe.connect(inputnode, 'SS_T2',
                         data_preparation_pipe, 'inputnode.SS_T2')
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

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['debiased_T1', 'debiased_T2',
                                      "brain_mask"]),
        name='outputnode')

    assert not ("correct_bias_pipe" in params.keys() and "N4debias" in
                params.keys()), "error, only one of correct_bias_pipe\
                or N4debias should be present"

    if "correct_bias_pipe" in params.keys():
        # Correct_bias_T1_T2
        correct_bias_pipe = create_correct_bias_pipe(
            params=parse_key(params, "correct_bias_pipe"))

        brain_extraction_pipe.connect(inputnode, 'preproc_T1',
                                      correct_bias_pipe,
                                      'inputnode.preproc_T1')
        brain_extraction_pipe.connect(inputnode, 'preproc_T2',
                                      correct_bias_pipe,
                                      'inputnode.preproc_T2')

        brain_extraction_pipe.connect(correct_bias_pipe,
                                      "outputnode.debiased_T1",
                                      outputnode, "debiased_T1")
        brain_extraction_pipe.connect(correct_bias_pipe,
                                      "outputnode.debiased_T2",
                                      outputnode, "debiased_T2")

        # brain extraction
        extract_pipe = create_extract_pipe(
            params_template=params_template,
            params=parse_key(params, "extract_pipe"))

        brain_extraction_pipe.connect(correct_bias_pipe,
                                      "outputnode.debiased_T1",
                                      extract_pipe, "inputnode.restore_T1")
        brain_extraction_pipe.connect(correct_bias_pipe,
                                      "outputnode.debiased_T2",
                                      extract_pipe, "inputnode.restore_T2")
        brain_extraction_pipe.connect(inputnode, "indiv_params",
                                      extract_pipe, "inputnode.indiv_params")

        brain_extraction_pipe.connect(extract_pipe,
                                      "smooth_mask.out_file",
                                      outputnode, "brain_mask")

    elif "N4debias" in params.keys():
        print("Found N4debias in params.json")

        # N4 intensity normalization over T1
        N4debias_T1 = NodeParams(ants.N4BiasFieldCorrection(),
                                 params=parse_key(params, "N4debias"),
                                 name='N4debias_T1')

        brain_extraction_pipe.connect(inputnode, 'preproc_T1',
                                      N4debias_T1, "input_image")

        brain_extraction_pipe.connect(
            inputnode, ('indiv_params', parse_key, "N4debias"),
            N4debias_T1, "indiv_params")

        brain_extraction_pipe.connect(N4debias_T1, "output_image",
                                      outputnode, "debiased_T1")

        # N4 intensity normalization over T2
        N4debias_T2 = NodeParams(ants.N4BiasFieldCorrection(),
                                 params=parse_key(params, "N4debias"),
                                 name='N4debias_T2')

        brain_extraction_pipe.connect(inputnode, 'preproc_T2',
                                      N4debias_T2, "input_image")

        brain_extraction_pipe.connect(
            inputnode, ('indiv_params', parse_key, "N4debias"),
            N4debias_T2, "indiv_params")

        brain_extraction_pipe.connect(N4debias_T2, "output_image",
                                      outputnode, "debiased_T2")

        # brain extraction
        extract_pipe = create_extract_pipe(
            params_template=params_template,
            params=parse_key(params, "extract_pipe"))

        brain_extraction_pipe.connect(N4debias_T1, "output_image",
                                      extract_pipe, "inputnode.restore_T1")
        brain_extraction_pipe.connect(N4debias_T2, "output_image",
                                      extract_pipe, "inputnode.restore_T2")
        brain_extraction_pipe.connect(inputnode, "indiv_params",
                                      extract_pipe, "inputnode.indiv_params")

        brain_extraction_pipe.connect(extract_pipe,
                                      "smooth_mask.out_file",
                                      outputnode, "brain_mask")
    elif "fast" in params.keys():

        print("Found fast in params.json")

        # fast over T1
        fast_T1 = NodeParams(
            fsl.FAST(),
            params=parse_key(params, "fast"),
            name='fast_T1')

        fast_T1.inputs.output_biascorrected = True
        fast_T1.inputs.output_biasfield = True

        brain_extraction_pipe.connect(inputnode, 'preproc_T1',
                                      fast_T1, "in_files")

        brain_extraction_pipe.connect(
            inputnode, ('indiv_params', parse_key, "fast"),
            fast_T1, "indiv_params")

        brain_extraction_pipe.connect(fast_T1, "restored_image",
                                      outputnode, "debiased_T1")

        # fast over T2
        fast_T2 = NodeParams(
            fsl.FAST(),
            params=parse_key(params, "fast"),
            name='fast_T2')

        fast_T2.inputs.output_biascorrected = True
        fast_T2.inputs.output_biasfield = True

        brain_extraction_pipe.connect(inputnode, 'preproc_T2',
                                      fast_T2, "in_files")

        brain_extraction_pipe.connect(
            inputnode, ('indiv_params', parse_key, "fast"),
            fast_T2, "indiv_params")

        brain_extraction_pipe.connect(fast_T2, "restored_image",
                                      outputnode, "debiased_T2")
        # brain extraction
        extract_pipe = create_extract_pipe(
            params_template=params_template,
            params=parse_key(params, "extract_pipe"))

        brain_extraction_pipe.connect(fast_T1, ("restored_image", show_files),
                                      extract_pipe, "inputnode.restore_T1")
        brain_extraction_pipe.connect(fast_T2, ("restored_image", show_files),
                                      extract_pipe, "inputnode.restore_T2")
        brain_extraction_pipe.connect(inputnode, "indiv_params",
                                      extract_pipe, "inputnode.indiv_params")

        brain_extraction_pipe.connect(extract_pipe,
                                      "smooth_mask.out_file",
                                      outputnode, "brain_mask")
    else:
        print("No debias will be performed before extract_pipe")

        # brain extraction
        extract_pipe = create_extract_pipe(
            params_template=params_template,
            params=parse_key(params, "extract_pipe"))

        brain_extraction_pipe.connect(inputnode, "preproc_T1",
                                      extract_pipe, "inputnode.restore_T1")
        brain_extraction_pipe.connect(inputnode, "preproc_T2",
                                      extract_pipe, "inputnode.restore_T2")
        brain_extraction_pipe.connect(inputnode, "indiv_params",
                                      extract_pipe, "inputnode.indiv_params")

        brain_extraction_pipe.connect(extract_pipe,
                                      "smooth_mask.out_file",
                                      outputnode, "brain_mask")

    return brain_extraction_pipe


def create_brain_segment_from_mask_pipe(
        params_template, params={}, name="brain_segment_from_mask_pipe",
        space="native"):
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

    # creating outputnode
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["segmented_file", "threshold_gm", "threshold_wm",
                    "threshold_csf", "prob_gm", "prob_wm",
                    "prob_csf", "gen_5tt", "debiased_brain"]),
        name='outputnode')

    # correcting for bias T1/T2, but this time with a mask
    if "masked_correct_bias_pipe" in params.keys():
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

    elif "debias" in params.keys():
        # Bias correction of cropped images
        debias = NodeParams(T1xT2BiasFieldCorrection(),
                            params=parse_key(params, "debias"),
                            name='debias')

        brain_segment_pipe.connect(inputnode, 'preproc_T1',
                                   debias, 't1_file')
        brain_segment_pipe.connect(inputnode, 'preproc_T2',
                                   debias, 't2_file')
        brain_segment_pipe.connect(inputnode, 'brain_mask',
                                   debias, 'b')
        # TODO is not used now...
        brain_segment_pipe.connect(
            inputnode, ('indiv_params', parse_key, "debias"),
            debias, 'indiv_params')

    else:
        print("**** Error, masked_correct_bias_pipe or debias \
            should be in brain_extraction_pipe of params.json")
        print("No T1*T2 debias will be performed")

    # register NMT template, template mask and priors to subject T1
    register_NMT_pipe = create_register_NMT_pipe(
        params_template=params_template,
        params=parse_key(params, "register_NMT_pipe"))

    if "masked_correct_bias_pipe" in params.keys():
        brain_segment_pipe.connect(
            masked_correct_bias_pipe, 'outputnode.mask_debiased_T1',
            register_NMT_pipe, "inputnode.T1")

    elif "debias" in params.keys():
        brain_segment_pipe.connect(
            debias, 't1_debiased_brain_file',
            register_NMT_pipe, "inputnode.T1")

    else:
        brain_segment_pipe.connect(
            inputnode, 'preproc_T1',
            register_NMT_pipe, "inputnode.T1")

    brain_segment_pipe.connect(
        inputnode, 'indiv_params',
        register_NMT_pipe, "inputnode.indiv_params")

    # ants Atropos
    if "template_seg" in params_template.keys():

        print("#### create_segment_atropos_seg_pipe ")
        segment_atropos_pipe = create_segment_atropos_seg_pipe(
            params=parse_key(params, "segment_atropos_pipe"))

        brain_segment_pipe.connect(
            register_NMT_pipe, 'align_seg.out_file', segment_atropos_pipe,
            "inputnode.seg_file")

    else:
        print("#### create_segment_atropos_pipe (3 tissues) ")

        segment_atropos_pipe = create_segment_atropos_pipe(
            params=parse_key(params, "segment_atropos_pipe"))

        # linking priors if "use_priors" in params
        if "use_priors" in params["segment_atropos_pipe"].keys():

            brain_segment_pipe.connect(
                register_NMT_pipe, 'align_seg_csf.out_file',
                segment_atropos_pipe, "inputnode.csf_prior_file")
            brain_segment_pipe.connect(
                register_NMT_pipe, 'align_seg_gm.out_file',
                segment_atropos_pipe, "inputnode.gm_prior_file")
            brain_segment_pipe.connect(
                register_NMT_pipe, 'align_seg_wm.out_file',
                segment_atropos_pipe, "inputnode.wm_prior_file")

    # input to segment_atropos_pipe depending on T1T2 debias step
    if "masked_correct_bias_pipe" in params.keys():
        brain_segment_pipe.connect(
            masked_correct_bias_pipe, 'outputnode.mask_debiased_T1',
            segment_atropos_pipe, "inputnode.brain_file")
    elif "debias" in params.keys():
        brain_segment_pipe.connect(
            debias, 't1_debiased_brain_file',
            segment_atropos_pipe, "inputnode.brain_file")
    else:
        brain_segment_pipe.connect(
            inputnode, 'preproc_T1',
            segment_atropos_pipe, "inputnode.brain_file")

    if "export_5tt_pipe" in params.keys():

        export_5tt_pipe = create_5tt_pipe(
            params=parse_key(params, "export_5tt_pipe"))

        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.threshold_gm',
                                   export_5tt_pipe, 'inputnode.gm_file')

        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.threshold_wm',
                                   export_5tt_pipe, 'inputnode.wm_file')

        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.threshold_csf',
                                   export_5tt_pipe, 'inputnode.csf_file')

        brain_segment_pipe.connect(export_5tt_pipe, 'export_5tt.gen_5tt_file',
                                   outputnode, 'gen_5tt')

    # output prepreocessed brain T1
    if "masked_correct_bias_pipe" in params.keys():
        brain_segment_pipe.connect(
            masked_correct_bias_pipe, 'outputnode.mask_debiased_T1',
            outputnode, 'debiased_brain')
    elif "debias" in params.keys():
        brain_segment_pipe.connect(debias, 't1_debiased_brain_file',
                                   outputnode, 'debiased_brain')
    else:

        brain_segment_pipe.connect(inputnode, 'preproc_T1',
                                   outputnode, 'debiased_brain')

    if space == 'native':

        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.segmented_file',
                                   outputnode, 'segmented_file')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.threshold_gm',
                                   outputnode, 'threshold_gm')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.threshold_wm',
                                   outputnode, 'threshold_wm')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.threshold_csf',
                                   outputnode, 'threshold_csf')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.prob_gm',
                                   outputnode, 'prob_gm')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.prob_wm',
                                   outputnode, 'prob_wm')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.prob_csf',
                                   outputnode, 'prob_csf')

    elif space == "template":
        reg_seg_pipe = create_reg_seg_pipe()

        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.segmented_file',
                                   reg_seg_pipe,
                                   'inputnode.native_seg')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.threshold_gm',
                                   reg_seg_pipe,
                                   'inputnode.native_threshold_gm')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.threshold_wm',
                                   reg_seg_pipe,
                                   'inputnode.native_threshold_wm')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.threshold_csf',
                                   reg_seg_pipe,
                                   'inputnode.native_threshold_csf')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.prob_gm',
                                   reg_seg_pipe,
                                   'inputnode.native_prob_gm')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.prob_wm',
                                   reg_seg_pipe,
                                   'inputnode.native_prob_wm')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.prob_csf',
                                   reg_seg_pipe,
                                   'inputnode.native_prob_csf')

        # other inputs
        brain_segment_pipe.connect(register_NMT_pipe,
                                   'NMT_subject_align.transfo_file',
                                   reg_seg_pipe, 'inputnode.transfo_file')

        reg_seg_pipe.inputs.inputnode.ref_image = \
            params_template['template_head']

        # output node
        brain_segment_pipe.connect(reg_seg_pipe, 'outputnode.norm_seg',
                                   outputnode, 'segmented_file')
        brain_segment_pipe.connect(reg_seg_pipe,
                                   'outputnode.norm_threshold_gm',
                                   outputnode, 'threshold_gm')
        brain_segment_pipe.connect(reg_seg_pipe,
                                   'outputnode.norm_threshold_wm',
                                   outputnode, 'threshold_wm')
        brain_segment_pipe.connect(reg_seg_pipe,
                                   'outputnode.norm_threshold_csf',
                                   outputnode, 'threshold_csf')
        brain_segment_pipe.connect(reg_seg_pipe, 'outputnode.norm_prob_gm',
                                   outputnode, 'prob_gm')
        brain_segment_pipe.connect(reg_seg_pipe, 'outputnode.norm_prob_wm',
                                   outputnode, 'prob_wm')
        brain_segment_pipe.connect(reg_seg_pipe, 'outputnode.norm_prob_csf',
                                   outputnode, 'prob_csf')

    return brain_segment_pipe


def create_full_ants_subpipes(
        params_template, params_template_aladin, params={},
        name="full_ants_subpipes", mask_file=None,
        space="native", pad=False):
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
        niu.IdentityInterface(
            fields=['brain_mask', 'segmented_brain_mask', 'prob_gm', 'prob_wm',
                    'prob_csf', "gen_5tt", "debiased_brain", "debiased_T1"]),
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
            params=parse_key(params, "short_preparation_pipe"),
            params_template=params_template_aladin)

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

        if pad:

            if "short_preparation_pipe" in params.keys():
                if "crop_T1" in params["short_preparation_pipe"].keys():

                    print("Padding mask in native space")

                    pad_mask = pe.Node(
                        niu.Function(
                            input_names=['cropped_img_file', 'orig_img_file',
                                         'indiv_crop'],
                            output_names=['padded_img_file'],
                            function=padding_cropped_img),
                        name="pad_mask")

                    seg_pipe.connect(brain_extraction_pipe,
                                     "outputnode.brain_mask",
                                     pad_mask, "cropped_img_file")

                    seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                     pad_mask, "orig_img_file")

                    seg_pipe.connect(inputnode, "indiv_params",
                                     pad_mask, "indiv_crop")

                    seg_pipe.connect(pad_mask, "padded_img_file",
                                     outputnode, "brain_mask")

                    print("Padding debiased_T1 in native space")

                    pad_debiased_T1 = pe.Node(
                        niu.Function(
                            input_names=['cropped_img_file', 'orig_img_file',
                                         'indiv_crop'],
                            output_names=['padded_img_file'],
                            function=padding_cropped_img),
                        name="pad_debiased_T1")

                    seg_pipe.connect(brain_extraction_pipe,
                                     "outputnode.debiased_T1",
                                     pad_debiased_T1, "cropped_img_file")

                    seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                     pad_debiased_T1, "orig_img_file")

                    seg_pipe.connect(inputnode, "indiv_params",
                                     pad_debiased_T1, "indiv_crop")

                    seg_pipe.connect(pad_debiased_T1, "padded_img_file",
                                     outputnode, "debiased_T1")

                elif "bet_crop" in params["short_preparation_pipe"].keys():
                    print("Not implemented yet")

                else:
                    print("Using reg_aladin transfo to pad mask back")
                    pad_mask = pe.Node(regutils.RegResample(),
                                       name="pad_mask")

                    seg_pipe.connect(brain_extraction_pipe,
                                     "outputnode.brain_mask",
                                     pad_mask, "flo_file")

                    seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                     pad_mask, "ref_file")

                    seg_pipe.connect(data_preparation_pipe,
                                     "inv_tranfo.out_file",
                                     pad_mask, "trans_file")

                    print("Using reg_aladin transfo to pad debiased_T1 back")
                    pad_debiased_T1 = pe.Node(regutils.RegResample(),
                                              name="pad_debiased_T1")

                    seg_pipe.connect(brain_extraction_pipe,
                                     "outputnode.debiased_T1",
                                     pad_debiased_T1, "flo_file")

                    seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                     pad_debiased_T1, "ref_file")

                    seg_pipe.connect(data_preparation_pipe,
                                     "inv_tranfo.out_file",
                                     pad_debiased_T1, "trans_file")

                    # outputnode
                    seg_pipe.connect(pad_mask, "out_file",
                                     outputnode, "brain_mask")

                    seg_pipe.connect(pad_debiased_T1, "out_file",
                                     outputnode, "debiased_T1")

        else:
            seg_pipe.connect(brain_extraction_pipe, "outputnode.brain_mask",
                             outputnode, "brain_mask")

            seg_pipe.connect(brain_extraction_pipe, "outputnode.debiased_T1",
                             outputnode, "debiased_T1")

    # full_segment (restarting from the avg_align files)
    if "brain_segment_pipe" not in params.keys():
        return seg_pipe

    brain_segment_pipe = create_brain_segment_from_mask_pipe(
        params_template=params_template,
        params=parse_key(params, "brain_segment_pipe"), space=space)

    seg_pipe.connect(brain_extraction_pipe, "outputnode.debiased_T1",
                     brain_segment_pipe, 'inputnode.preproc_T1')
    seg_pipe.connect(brain_extraction_pipe, "outputnode.debiased_T2",
                     brain_segment_pipe, 'inputnode.preproc_T2')

    if mask_file is None:

        seg_pipe.connect(brain_extraction_pipe,
                         "outputnode.brain_mask",
                         brain_segment_pipe, "inputnode.brain_mask")
    else:

        brain_segment_pipe.inputs.inputnode.brain_mask = mask_file

    seg_pipe.connect(inputnode, 'indiv_params',
                     brain_segment_pipe, 'inputnode.indiv_params')

    if pad and space == "native":
        if "short_preparation_pipe" in params.keys():
            if "crop_T1" in params["short_preparation_pipe"].keys():

                print("Padding seg_mask in native space")

                pad_seg_mask = pe.Node(
                    niu.Function(
                        input_names=['cropped_img_file', 'orig_img_file',
                                     'indiv_crop'],
                        output_names=['padded_img_file'],
                        function=padding_cropped_img),
                    name="pad_seg_mask")

                seg_pipe.connect(brain_segment_pipe,
                                 "outputnode.segmented_file",
                                 pad_seg_mask, "cropped_img_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_seg_mask, "orig_img_file")

                seg_pipe.connect(inputnode, "indiv_params",
                                 pad_seg_mask, "indiv_crop")

                seg_pipe.connect(pad_seg_mask, "padded_img_file",
                                 outputnode, "segmented_brain_mask")

            elif "bet_crop" in params["short_preparation_pipe"].keys():
                print("Not implemented yet")

            else:
                print("Using reg_aladin transfo to pad seg_mask back")

                pad_seg_mask = pe.Node(regutils.RegResample(),
                                       name="pad_seg_mask")

                seg_pipe.connect(brain_segment_pipe,
                                 "outputnode.segmented_file",
                                 pad_seg_mask, "flo_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_seg_mask, "ref_file")

                seg_pipe.connect(data_preparation_pipe, "inv_tranfo.out_file",
                                 pad_seg_mask, "trans_file")

                # outputnode
                seg_pipe.connect(pad_seg_mask, "out_file",
                                 outputnode, "segmented_brain_mask")

    else:
        seg_pipe.connect(brain_segment_pipe, 'outputnode.segmented_file',
                         outputnode, 'segmented_brain_mask')

    if pad and space == "native":
        if "short_preparation_pipe" in params.keys():
            if "crop_T1" in params["short_preparation_pipe"].keys():

                print("Padding debiased_brain in native space")

                pad_debiased_brain = pe.Node(
                    niu.Function(
                        input_names=['cropped_img_file', 'orig_img_file',
                                     'indiv_crop'],
                        output_names=['padded_img_file'],
                        function=padding_cropped_img),
                    name="pad_debiased_brain")

                seg_pipe.connect(brain_segment_pipe,
                                 "outputnode.debiased_brain",
                                 pad_debiased_brain, "cropped_img_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_debiased_brain, "orig_img_file")

                seg_pipe.connect(inputnode, "indiv_params",
                                 pad_debiased_brain, "indiv_crop")

                seg_pipe.connect(pad_debiased_brain, "padded_img_file",
                                 outputnode, "debiased_brain")

            elif "bet_crop" in params["short_preparation_pipe"].keys():
                print("Not implemented yet")

            else:
                print("Using reg_aladin transfo to pad debiased_brain back")

                pad_debiased_brain = pe.Node(regutils.RegResample(),
                                             name="pad_debiased_brain")

                seg_pipe.connect(brain_segment_pipe,
                                 "outputnode.debiased_brain",
                                 pad_debiased_brain, "flo_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_debiased_brain, "ref_file")

                seg_pipe.connect(data_preparation_pipe,
                                 "inv_tranfo.out_file",
                                 pad_debiased_brain, "trans_file")

                # outputnode
                seg_pipe.connect(pad_debiased_brain, "out_file",
                                 outputnode, "debiased_brain")

    else:
        seg_pipe.connect(brain_segment_pipe, 'outputnode.debiased_brain',
                         outputnode, 'debiased_brain')

    if pad and space == "native":
        if "short_preparation_pipe" in params.keys():
            if "crop_T1" in params["short_preparation_pipe"].keys():

                print("Padding prob_csf in native space")

                pad_prob_csf = pe.Node(
                    niu.Function(
                        input_names=['cropped_img_file', 'orig_img_file',
                                     'indiv_crop'],
                        output_names=['padded_img_file'],
                        function=padding_cropped_img),
                    name="pad_prob_csf")

                seg_pipe.connect(brain_segment_pipe, "outputnode.prob_csf",
                                 pad_prob_csf, "cropped_img_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_prob_csf, "orig_img_file")

                seg_pipe.connect(inputnode, "indiv_params",
                                 pad_prob_csf, "indiv_crop")

                seg_pipe.connect(pad_prob_csf, "padded_img_file",
                                 outputnode, "prob_csf")

            elif "bet_crop" in params["short_preparation_pipe"].keys():
                print("Not implemented yet")

            else:
                print("Using reg_aladin transfo to pad prob_csf back")

                pad_prob_csf = pe.Node(regutils.RegResample(),
                                       name="pad_prob_csf")

                seg_pipe.connect(brain_segment_pipe, "outputnode.prob_csf",
                                 pad_prob_csf, "flo_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_prob_csf, "ref_file")

                seg_pipe.connect(data_preparation_pipe,
                                 "inv_tranfo.out_file",
                                 pad_prob_csf, "trans_file")

                # outputnode
                seg_pipe.connect(pad_prob_csf, "out_file",
                                 outputnode, "prob_csf")

    else:
        seg_pipe.connect(brain_segment_pipe, 'outputnode.prob_csf',
                         outputnode, 'prob_csf')

    if pad and space == "native":
        if "short_preparation_pipe" in params.keys():
            if "crop_T1" in params["short_preparation_pipe"].keys():

                print("Padding prob_gm in native space")

                pad_prob_gm = pe.Node(
                    niu.Function(
                        input_names=['cropped_img_file', 'orig_img_file',
                                     'indiv_crop'],
                        output_names=['padded_img_file'],
                        function=padding_cropped_img),
                    name="pad_prob_gm")

                seg_pipe.connect(brain_segment_pipe, "outputnode.prob_gm",
                                 pad_prob_gm, "cropped_img_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_prob_gm, "orig_img_file")

                seg_pipe.connect(inputnode, "indiv_params",
                                 pad_prob_gm, "indiv_crop")

                seg_pipe.connect(pad_prob_gm, "padded_img_file",
                                 outputnode, "prob_gm")

            elif "bet_crop" in params["short_preparation_pipe"].keys():
                print("Not implemented yet")

            else:
                print("Using reg_aladin transfo to pad prob_gm back")

                pad_prob_gm = pe.Node(regutils.RegResample(),
                                      name="pad_prob_gm")

                seg_pipe.connect(brain_segment_pipe, "outputnode.prob_gm",
                                 pad_prob_gm, "flo_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_prob_gm, "ref_file")

                seg_pipe.connect(data_preparation_pipe,
                                 "inv_tranfo.out_file",
                                 pad_prob_gm, "trans_file")

                # outputnode
                seg_pipe.connect(pad_prob_gm, "out_file",
                                 outputnode, "prob_gm")

    else:
        seg_pipe.connect(brain_segment_pipe, 'outputnode.prob_gm',
                         outputnode, 'prob_gm')

    if pad and space == "native":
        if "short_preparation_pipe" in params.keys():
            if "crop_T1" in params["short_preparation_pipe"].keys():

                print("Padding prob_wm in native space")

                pad_prob_wm = pe.Node(
                    niu.Function(
                        input_names=['cropped_img_file', 'orig_img_file',
                                     'indiv_crop'],
                        output_names=['padded_img_file'],
                        function=padding_cropped_img),
                    name="pad_prob_wm")

                seg_pipe.connect(brain_segment_pipe, "outputnode.prob_wm",
                                 pad_prob_wm, "cropped_img_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_prob_wm, "orig_img_file")

                seg_pipe.connect(inputnode, "indiv_params",
                                 pad_prob_wm, "indiv_crop")

                seg_pipe.connect(pad_prob_wm, "padded_img_file",
                                 outputnode, "prob_wm")

            elif "bet_crop" in params["short_preparation_pipe"].keys():
                print("Not implemented yet")

            else:
                print("Using reg_aladin transfo to pad prob_wm back")

                pad_prob_wm = pe.Node(regutils.RegResample(),
                                      name="pad_prob_wm")

                seg_pipe.connect(brain_segment_pipe, "outputnode.prob_wm",
                                 pad_prob_wm, "flo_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_prob_wm, "ref_file")

                seg_pipe.connect(data_preparation_pipe,
                                 "inv_tranfo.out_file",
                                 pad_prob_wm, "trans_file")

                # outputnode
                seg_pipe.connect(pad_prob_wm, "out_file",
                                 outputnode, "prob_wm")

    else:
        seg_pipe.connect(brain_segment_pipe, 'outputnode.prob_wm',
                         outputnode, 'prob_wm')

    if "export_5tt_pipe" in params["brain_segment_pipe"]:
        if pad and space == "native":
            if "short_preparation_pipe" in params.keys():
                if "crop_T1" in params["short_preparation_pipe"].keys():

                    print("Padding gen_5tt in native space")

                    pad_gen_5tt = pe.Node(
                        niu.Function(
                            input_names=['cropped_img_file', 'orig_img_file',
                                         'indiv_crop'],
                            output_names=['padded_img_file'],
                            function=padding_cropped_img),
                        name="pad_gen_5tt")

                    seg_pipe.connect(brain_segment_pipe, "outputnode.gen_5tt",
                                     pad_gen_5tt, "cropped_img_file")

                    seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                     pad_gen_5tt, "orig_img_file")

                    seg_pipe.connect(inputnode, "indiv_params",
                                     pad_gen_5tt, "indiv_crop")

                    seg_pipe.connect(pad_gen_5tt, "padded_img_file",
                                     outputnode, "gen_5tt")

                elif "bet_crop" in params["short_preparation_pipe"].keys():
                    print("Not implemented yet")

                else:
                    print("Using reg_aladin transfo to pad gen_5tt back")

                    pad_gen_5tt = pe.Node(regutils.RegResample(),
                                          name="pad_gen_5tt")

                    seg_pipe.connect(brain_segment_pipe, "outputnode.gen_5tt",
                                     pad_gen_5tt, "flo_file")

                    seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                     pad_gen_5tt, "ref_file")

                    seg_pipe.connect(data_preparation_pipe,
                                     "inv_tranfo.out_file",
                                     pad_gen_5tt, "trans_file")

                    # outputnode
                    seg_pipe.connect(pad_gen_5tt, "out_file",
                                     outputnode, "gen_5tt")

        else:
            seg_pipe.connect(brain_segment_pipe, 'outputnode.gen_5tt',
                             outputnode, 'gen_5tt')

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
                         'outputnode.debiased_T1',
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

    # Creating output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['debiased_T1', "brain_mask"]),
        name='outputnode')

    if "N4debias" in params.keys():

        print("Found N4debias in params.json")

        # N4 intensity normalization over T1
        N4debias_T1 = NodeParams(ants.N4BiasFieldCorrection(),
                                 params=parse_key(params, "N4debias"),
                                 name='N4debias_T1')

        brain_extraction_pipe.connect(inputnode, 'preproc_T1',
                                      N4debias_T1, "input_image")

        brain_extraction_pipe.connect(
            inputnode, ('indiv_params', parse_key, "N4debias"),
            N4debias_T1, "indiv_params")

        brain_extraction_pipe.connect(N4debias_T1, "output_image",
                                      outputnode, "debiased_T1")

        # brain extraction
        extract_T1_pipe = create_extract_T1_pipe(
            params_template=params_template,
            params=parse_key(params, "extract_pipe"))

        brain_extraction_pipe.connect(N4debias_T1, "output_image",
                                      extract_T1_pipe, "inputnode.restore_T1")

        brain_extraction_pipe.connect(
            inputnode, "indiv_params",
            extract_T1_pipe, "inputnode.indiv_params")

        brain_extraction_pipe.connect(extract_T1_pipe,
                                      "smooth_mask.out_file",
                                      outputnode, "brain_mask")

    elif "fast" in params.keys():

        print("Found fast in params.json")

        # fast over T1
        fast_T1 = NodeParams(
            fsl.FAST(),
            params=parse_key(params, "fast"),
            name='fast_T1')

        fast_T1.inputs.output_biascorrected = True
        fast_T1.inputs.output_biasfield = True

        brain_extraction_pipe.connect(inputnode, 'preproc_T1',
                                      fast_T1, "in_files")

        brain_extraction_pipe.connect(
            inputnode, ('indiv_params', parse_key, "fast"),
            fast_T1, "indiv_params")

        brain_extraction_pipe.connect(fast_T1, "restored_image",
                                      outputnode, "debiased_T1")

        # brain extraction
        extract_T1_pipe = create_extract_T1_pipe(
            params_template=params_template,
            params=parse_key(params, "extract_pipe"))

        brain_extraction_pipe.connect(
            fast_T1, ("restored_image", show_files),
            extract_T1_pipe, "inputnode.restore_T1")

        brain_extraction_pipe.connect(
            inputnode, "indiv_params",
            extract_T1_pipe, "inputnode.indiv_params")

        brain_extraction_pipe.connect(extract_T1_pipe,
                                      "smooth_mask.out_file",
                                      outputnode, "brain_mask")

    else:

        brain_extraction_pipe.connect(inputnode, "preproc_T1",
                                      outputnode, "debiased_T1")

        # brain extraction (with atlasbrex)
        extract_T1_pipe = create_extract_T1_pipe(
            params_template=params_template,
            params=parse_key(params, "extract_pipe"))

        brain_extraction_pipe.connect(
            inputnode, "preproc_T1",
            extract_T1_pipe, "inputnode.restore_T1")

        brain_extraction_pipe.connect(
            inputnode, "indiv_params",
            extract_T1_pipe, "inputnode.indiv_params")

        brain_extraction_pipe.connect(extract_T1_pipe,
                                      "smooth_mask.out_file",
                                      outputnode, "brain_mask")

    return brain_extraction_pipe


def create_brain_segment_from_mask_T1_pipe(
        params_template, params={}, name="brain_segment_from_mask_T1_pipe",
        space="native"):
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
            fields=['debiased_T1', 'brain_mask', 'indiv_params']),
        name='inputnode')

    # creating outputnode
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["segmented_file", "threshold_gm", "threshold_wm",
                    "threshold_csf", "prob_gm", "prob_wm",
                    "prob_csf", "gen_5tt", "debiased_brain"]),
        name='outputnode')

    # mask T1 using brain mask and perform N4 bias correction

    # restore_mask_T1
    restore_mask_T1 = pe.Node(fsl.ApplyMask(), name='restore_mask_T1')

    brain_segment_pipe.connect(inputnode, 'debiased_T1',
                               restore_mask_T1, 'in_file')
    brain_segment_pipe.connect(inputnode, 'brain_mask',
                               restore_mask_T1, 'mask_file')

    # register NMT template, template mask and priors to subject T1
    register_NMT_pipe = create_register_NMT_pipe(
        params_template=params_template,
        params=parse_key(params, "register_NMT_pipe"))

    brain_segment_pipe.connect(
        restore_mask_T1, 'out_file',
        register_NMT_pipe, "inputnode.T1")
    brain_segment_pipe.connect(
        inputnode, 'indiv_params',
        register_NMT_pipe, "inputnode.indiv_params")

    # ants Atropos
    if "template_seg" in params_template.keys():

        print("#### create_segment_atropos_seg_pipe ")
        segment_atropos_pipe = create_segment_atropos_seg_pipe(
            params=parse_key(params, "segment_atropos_pipe"))

        brain_segment_pipe.connect(
            register_NMT_pipe, 'align_seg.out_file', segment_atropos_pipe,
            "inputnode.seg_file")

    else:
        segment_atropos_pipe = create_segment_atropos_pipe(
            params=parse_key(params, "segment_atropos_pipe"))

        if "use_priors" in params["segment_atropos_pipe"].keys():

            brain_segment_pipe.connect(register_NMT_pipe,
                                       'align_seg_csf.out_file',
                                       segment_atropos_pipe,
                                       "inputnode.csf_prior_file")

            brain_segment_pipe.connect(register_NMT_pipe,
                                       'align_seg_gm.out_file',
                                       segment_atropos_pipe,
                                       "inputnode.gm_prior_file")

            brain_segment_pipe.connect(register_NMT_pipe,
                                       'align_seg_wm.out_file',
                                       segment_atropos_pipe,
                                       "inputnode.wm_prior_file")
    # brain_file
    brain_segment_pipe.connect(restore_mask_T1, 'out_file',
                               segment_atropos_pipe, "inputnode.brain_file")

    if "export_5tt_pipe" in params.keys():

        export_5tt_pipe = create_5tt_pipe(
            params=parse_key(params, "export_5tt_pipe"))

        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.threshold_gm',
                                   export_5tt_pipe, 'inputnode.gm_file')

        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.threshold_wm',
                                   export_5tt_pipe, 'inputnode.wm_file')

        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.threshold_csf',
                                   export_5tt_pipe, 'inputnode.csf_file')

        brain_segment_pipe.connect(export_5tt_pipe, 'export_5tt.gen_5tt_file',
                                   outputnode, 'gen_5tt')

    # output prepreocessed brain T1
    brain_segment_pipe.connect(
        restore_mask_T1, 'out_file',
        outputnode, 'debiased_brain')

    if space == 'native':

        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.segmented_file',
                                   outputnode, 'segmented_file')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.threshold_gm',
                                   outputnode, 'threshold_gm')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.threshold_wm',
                                   outputnode, 'threshold_wm')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.threshold_csf',
                                   outputnode, 'threshold_csf')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.prob_gm',
                                   outputnode, 'prob_gm')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.prob_wm',
                                   outputnode, 'prob_wm')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.prob_csf',
                                   outputnode, 'prob_csf')
    elif space == "template":

        reg_seg_pipe = create_reg_seg_pipe()

        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.segmented_file',
                                   reg_seg_pipe,
                                   'inputnode.native_seg')

        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.threshold_gm',
                                   reg_seg_pipe,
                                   'inputnode.native_threshold_gm')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.threshold_wm',
                                   reg_seg_pipe,
                                   'inputnode.native_threshold_wm')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.threshold_csf',
                                   reg_seg_pipe,
                                   'inputnode.native_threshold_csf')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.prob_gm',
                                   reg_seg_pipe,
                                   'inputnode.native_prob_gm')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.prob_wm',
                                   reg_seg_pipe,
                                   'inputnode.native_prob_wm')
        brain_segment_pipe.connect(segment_atropos_pipe,
                                   'outputnode.prob_csf',
                                   reg_seg_pipe,
                                   'inputnode.native_prob_csf')

        # other inputs
        brain_segment_pipe.connect(register_NMT_pipe,
                                   'NMT_subject_align.transfo_file',
                                   reg_seg_pipe, 'inputnode.transfo_file')

        reg_seg_pipe.inputs.inputnode.ref_image = \
            params_template['template_head']

        # output node
        brain_segment_pipe.connect(reg_seg_pipe,
                                   'outputnode.norm_seg',
                                   outputnode, 'segmented_file')
        brain_segment_pipe.connect(reg_seg_pipe,
                                   'outputnode.norm_threshold_gm',
                                   outputnode, 'threshold_gm')
        brain_segment_pipe.connect(reg_seg_pipe,
                                   'outputnode.norm_threshold_wm',
                                   outputnode, 'threshold_wm')
        brain_segment_pipe.connect(reg_seg_pipe,
                                   'outputnode.norm_threshold_csf',
                                   outputnode, 'threshold_csf')
        brain_segment_pipe.connect(reg_seg_pipe, 'outputnode.norm_prob_gm',
                                   outputnode, 'prob_gm')
        brain_segment_pipe.connect(reg_seg_pipe, 'outputnode.norm_prob_wm',
                                   outputnode, 'prob_wm')
        brain_segment_pipe.connect(reg_seg_pipe, 'outputnode.norm_prob_csf',
                                   outputnode, 'prob_csf')

    return brain_segment_pipe


def create_full_T1_ants_subpipes(params_template, params_template_aladin,
                                 params={}, name="full_T1_ants_subpipes",
                                 space="native", pad=False):

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
        name='inputnode')

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=['brain_mask', 'segmented_brain_mask', 'prob_gm', 'prob_wm',
                    'prob_csf', "gen_5tt", "debiased_brain", "debiased_T1"]),
        name='outputnode')

    # preprocessing (perform preparation pipe with only T1)
    if 'short_preparation_pipe' in params.keys():
        data_preparation_pipe = create_short_preparation_T1_pipe(
            params=parse_key(params, "short_preparation_pipe"),
            params_template=params_template)

    else:
        print("Error, short_preparation_pipe was not found in params, \
            skipping")
        return seg_pipe

    seg_pipe.connect(inputnode, 'list_T1',
                     data_preparation_pipe, 'inputnode.list_T1')
    seg_pipe.connect(inputnode, 'indiv_params',
                     data_preparation_pipe, 'inputnode.indiv_params')

    # full extract brain pipeline (correct_bias, denoising, extract brain)
    if "brain_extraction_pipe" not in params.keys():
        print("Error, brain_extraction_pipe was not found in params, \
            skipping")
        return seg_pipe

    brain_extraction_pipe = create_brain_extraction_T1_pipe(
        params=parse_key(params, "brain_extraction_pipe"),
        params_template=params_template_aladin)

    seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                     brain_extraction_pipe, 'inputnode.preproc_T1')
    seg_pipe.connect(inputnode, 'indiv_params',
                     brain_extraction_pipe, 'inputnode.indiv_params')

    if pad and space == "native":

        if "short_preparation_pipe" in params.keys():
            if "crop_T1" in params["short_preparation_pipe"].keys():

                print("Padding mask in native space")
                pad_mask = pe.Node(
                    niu.Function(
                        input_names=['cropped_img_file', 'orig_img_file',
                                     'indiv_crop'],
                        output_names=['padded_img_file'],
                        function=padding_cropped_img),
                    name="pad_mask")

                seg_pipe.connect(brain_extraction_pipe,
                                 'outputnode.brain_mask',
                                 pad_mask, "cropped_img_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_mask, "orig_img_file")

                seg_pipe.connect(inputnode, "indiv_params",
                                 pad_mask, "indiv_crop")

                seg_pipe.connect(pad_mask, "padded_img_file",
                                 outputnode, "brain_mask")

                print("Padding debiased_T1 in native space")
                pad_debiased_T1 = pe.Node(
                    niu.Function(
                        input_names=['cropped_img_file', 'orig_img_file',
                                     'indiv_crop'],
                        output_names=['padded_img_file'],
                        function=padding_cropped_img),
                    name="pad_debiased_T1")

                seg_pipe.connect(brain_extraction_pipe,
                                 'outputnode.debiased_T1',
                                 pad_debiased_T1, "cropped_img_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_debiased_T1, "orig_img_file")

                seg_pipe.connect(inputnode, "indiv_params",
                                 pad_debiased_T1, "indiv_crop")

                seg_pipe.connect(pad_debiased_T1, "padded_img_file",
                                 outputnode, "debiased_T1")

            else:
                print("Using reg_aladin transfo to pad mask back")
                pad_mask = pe.Node(regutils.RegResample(), name="pad_mask")

                seg_pipe.connect(brain_extraction_pipe,
                                 "outputnode.brain_mask",
                                 pad_mask, "flo_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_mask, "ref_file")

                seg_pipe.connect(data_preparation_pipe, "inv_tranfo.out_file",
                                 pad_mask, "trans_file")

                print("Using reg_aladin transfo to pad debiased_T1 back")
                pad_debiased_T1 = pe.Node(regutils.RegResample(),
                                          name="pad_debiased_T1")

                seg_pipe.connect(brain_extraction_pipe,
                                 "outputnode.debiased_T1",
                                 pad_debiased_T1, "flo_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_debiased_T1, "ref_file")

                seg_pipe.connect(data_preparation_pipe, "inv_tranfo.out_file",
                                 pad_debiased_T1, "trans_file")

                # outputnode
                seg_pipe.connect(pad_mask, "out_file",
                                 outputnode, "brain_mask")

                seg_pipe.connect(pad_debiased_T1, "out_file",
                                 outputnode, "debiased_T1")
    else:
        seg_pipe.connect(brain_extraction_pipe,
                         "outputnode.brain_mask",
                         outputnode, "brain_mask")

        seg_pipe.connect(brain_extraction_pipe, "outputnode.debiased_T1",
                         outputnode, "debiased_T1")

    # full_segment (restarting from the avg_align files)
    if "brain_segment_pipe" not in params.keys():
        print("Error, brain_segment_pipe was not found in params, \
            skipping")
        return seg_pipe

    brain_segment_pipe = create_brain_segment_from_mask_T1_pipe(
        params_template=params_template,
        params=parse_key(params, "brain_segment_pipe"), space=space)

    seg_pipe.connect(brain_extraction_pipe, "outputnode.debiased_T1",
                     brain_segment_pipe, 'inputnode.debiased_T1')
    seg_pipe.connect(brain_extraction_pipe,
                     "extract_T1_pipe.smooth_mask.out_file",
                     brain_segment_pipe, "inputnode.brain_mask")
    seg_pipe.connect(inputnode, 'indiv_params',
                     brain_segment_pipe, 'inputnode.indiv_params')

    if pad and space == "native":
        if "short_preparation_pipe" in params.keys():
            if "crop_T1" in params["short_preparation_pipe"].keys():

                print("Padding seg_mask in native space")

                pad_seg_mask = pe.Node(
                    niu.Function(
                        input_names=['cropped_img_file', 'orig_img_file',
                                     'indiv_crop'],
                        output_names=['padded_img_file'],
                        function=padding_cropped_img),
                    name="pad_seg_mask")

                seg_pipe.connect(brain_segment_pipe,
                                 "outputnode.segmented_file",
                                 pad_seg_mask, "cropped_img_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_seg_mask, "orig_img_file")

                seg_pipe.connect(inputnode, "indiv_params",
                                 pad_seg_mask, "indiv_crop")

                seg_pipe.connect(pad_seg_mask, "padded_img_file",
                                 outputnode, "segmented_brain_mask")

            elif "bet_crop" in params["short_preparation_pipe"].keys():
                print("Not implemented yet")

            else:
                print("Using reg_aladin transfo to pad seg_mask back")

                pad_seg_mask = pe.Node(regutils.RegResample(),
                                       name="pad_seg_mask")

                seg_pipe.connect(brain_segment_pipe,
                                 "outputnode.segmented_file",
                                 pad_seg_mask, "flo_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_seg_mask, "ref_file")

                seg_pipe.connect(data_preparation_pipe, "inv_tranfo.out_file",
                                 pad_seg_mask, "trans_file")

                # outputnode
                seg_pipe.connect(pad_seg_mask, "out_file",
                                 outputnode, "segmented_brain_mask")

    else:
        seg_pipe.connect(brain_segment_pipe, 'outputnode.segmented_file',
                         outputnode, 'segmented_brain_mask')

    if pad and space == "native":
        if "short_preparation_pipe" in params.keys():
            if "crop_T1" in params["short_preparation_pipe"].keys():

                print("Padding debiased_brain in native space")

                pad_debiased_brain = pe.Node(
                    niu.Function(
                        input_names=['cropped_img_file', 'orig_img_file',
                                     'indiv_crop'],
                        output_names=['padded_img_file'],
                        function=padding_cropped_img),
                    name="pad_debiased_brain")

                seg_pipe.connect(brain_segment_pipe,
                                 "outputnode.debiased_brain",
                                 pad_debiased_brain, "cropped_img_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_debiased_brain, "orig_img_file")

                seg_pipe.connect(inputnode, "indiv_params",
                                 pad_debiased_brain, "indiv_crop")

                seg_pipe.connect(pad_debiased_brain, "padded_img_file",
                                 outputnode, "debiased_brain")

            elif "bet_crop" in params["short_preparation_pipe"].keys():
                print("Not implemented yet")

            else:
                print("Using reg_aladin transfo to pad debiased_brain back")

                pad_debiased_brain = pe.Node(regutils.RegResample(),
                                             name="pad_debiased_brain")

                seg_pipe.connect(brain_segment_pipe,
                                 "outputnode.debiased_brain",
                                 pad_debiased_brain, "flo_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_debiased_brain, "ref_file")

                seg_pipe.connect(data_preparation_pipe, "inv_tranfo.out_file",
                                 pad_debiased_brain, "trans_file")

                # outputnode
                seg_pipe.connect(pad_debiased_brain, "out_file",
                                 outputnode, "debiased_brain")

    else:
        seg_pipe.connect(brain_segment_pipe, 'outputnode.debiased_brain',
                         outputnode, 'debiased_brain')

    if pad and space == "native":
        if "short_preparation_pipe" in params.keys():
            if "crop_T1" in params["short_preparation_pipe"].keys():

                print("Padding prob_csf in native space")

                pad_prob_csf = pe.Node(
                    niu.Function(
                        input_names=['cropped_img_file', 'orig_img_file',
                                     'indiv_crop'],
                        output_names=['padded_img_file'],
                        function=padding_cropped_img),
                    name="pad_prob_csf")

                seg_pipe.connect(brain_segment_pipe, "outputnode.prob_csf",
                                 pad_prob_csf, "cropped_img_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_prob_csf, "orig_img_file")

                seg_pipe.connect(inputnode, "indiv_params",
                                 pad_prob_csf, "indiv_crop")

                seg_pipe.connect(pad_prob_csf, "padded_img_file",
                                 outputnode, "prob_csf")

            elif "bet_crop" in params["short_preparation_pipe"].keys():
                print("Not implemented yet")

            else:
                print("Using reg_aladin transfo to pad prob_csf back")

                pad_prob_csf = pe.Node(regutils.RegResample(),
                                       name="pad_prob_csf")

                seg_pipe.connect(brain_segment_pipe, "outputnode.prob_csf",
                                 pad_prob_csf, "flo_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_prob_csf, "ref_file")

                seg_pipe.connect(data_preparation_pipe, "inv_tranfo.out_file",
                                 pad_prob_csf, "trans_file")

                # outputnode
                seg_pipe.connect(pad_prob_csf, "out_file",
                                 outputnode, "prob_csf")

    else:
        seg_pipe.connect(brain_segment_pipe, 'outputnode.prob_csf',
                         outputnode, 'prob_csf')

    if pad and space == "native":
        if "short_preparation_pipe" in params.keys():
            if "crop_T1" in params["short_preparation_pipe"].keys():

                print("Padding prob_gm in native space")

                pad_prob_gm = pe.Node(
                    niu.Function(
                        input_names=['cropped_img_file', 'orig_img_file',
                                     'indiv_crop'],
                        output_names=['padded_img_file'],
                        function=padding_cropped_img),
                    name="pad_prob_gm")

                seg_pipe.connect(brain_segment_pipe, "outputnode.prob_gm",
                                 pad_prob_gm, "cropped_img_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_prob_gm, "orig_img_file")

                seg_pipe.connect(inputnode, "indiv_params",
                                 pad_prob_gm, "indiv_crop")

                seg_pipe.connect(pad_prob_gm, "padded_img_file",
                                 outputnode, "prob_gm")

            elif "bet_crop" in params["short_preparation_pipe"].keys():
                print("Not implemented yet")

            else:
                print("Using reg_aladin transfo to pad prob_gm back")

                pad_prob_gm = pe.Node(regutils.RegResample(),
                                      name="pad_prob_gm")

                seg_pipe.connect(brain_segment_pipe, "outputnode.prob_gm",
                                 pad_prob_gm, "flo_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_prob_gm, "ref_file")

                seg_pipe.connect(data_preparation_pipe, "inv_tranfo.out_file",
                                 pad_prob_gm, "trans_file")

                # outputnode
                seg_pipe.connect(pad_prob_gm, "out_file",
                                 outputnode, "prob_gm")

    else:
        seg_pipe.connect(brain_segment_pipe, 'outputnode.prob_gm',
                         outputnode, 'prob_gm')

    if pad and space == "native":
        if "short_preparation_pipe" in params.keys():
            if "crop_T1" in params["short_preparation_pipe"].keys():

                print("Padding prob_wm in native space")

                pad_prob_wm = pe.Node(
                    niu.Function(
                        input_names=['cropped_img_file', 'orig_img_file',
                                     'indiv_crop'],
                        output_names=['padded_img_file'],
                        function=padding_cropped_img),
                    name="pad_prob_wm")

                seg_pipe.connect(brain_segment_pipe, "outputnode.prob_wm",
                                 pad_prob_wm, "cropped_img_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_prob_wm, "orig_img_file")

                seg_pipe.connect(inputnode, "indiv_params",
                                 pad_prob_wm, "indiv_crop")

                seg_pipe.connect(pad_prob_wm, "padded_img_file",
                                 outputnode, "prob_wm")

            elif "bet_crop" in params["short_preparation_pipe"].keys():
                print("Not implemented yet")

            else:
                print("Using reg_aladin transfo to pad prob_wm back")

                pad_prob_wm = pe.Node(regutils.RegResample(),
                                      name="pad_prob_wm")

                seg_pipe.connect(brain_segment_pipe, "outputnode.prob_wm",
                                 pad_prob_wm, "flo_file")

                seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                 pad_prob_wm, "ref_file")

                seg_pipe.connect(data_preparation_pipe, "inv_tranfo.out_file",
                                 pad_prob_wm, "trans_file")

                # outputnode
                seg_pipe.connect(pad_prob_wm, "out_file",
                                 outputnode, "prob_wm")

    else:
        seg_pipe.connect(brain_segment_pipe, 'outputnode.prob_wm',
                         outputnode, 'prob_wm')

    if "export_5tt_pipe" in params["brain_segment_pipe"]:
        if pad and space == "native":
            if "short_preparation_pipe" in params.keys():
                if "crop_T1" in params["short_preparation_pipe"].keys():

                    print("Padding gen_5tt in native space")

                    pad_gen_5tt = pe.Node(
                        niu.Function(
                            input_names=['cropped_img_file', 'orig_img_file',
                                         'indiv_crop'],
                            output_names=['padded_img_file'],
                            function=padding_cropped_img),
                        name="pad_gen_5tt")

                    seg_pipe.connect(brain_segment_pipe, "outputnode.gen_5tt",
                                     pad_gen_5tt, "cropped_img_file")

                    seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                     pad_gen_5tt, "orig_img_file")

                    seg_pipe.connect(inputnode, "indiv_params",
                                     pad_gen_5tt, "indiv_crop")

                    seg_pipe.connect(pad_gen_5tt, "padded_img_file",
                                     outputnode, "gen_5tt")

                elif "bet_crop" in params["short_preparation_pipe"].keys():
                    print("Not implemented yet")

                else:
                    print("Using reg_aladin transfo to pad gen_5tt back")

                    pad_gen_5tt = pe.Node(regutils.RegResample(),
                                          name="pad_gen_5tt")

                    seg_pipe.connect(brain_segment_pipe, "outputnode.gen_5tt",
                                     pad_gen_5tt, "flo_file")

                    seg_pipe.connect(data_preparation_pipe, "av_T1.avg_img",
                                     pad_gen_5tt, "ref_file")

                    seg_pipe.connect(data_preparation_pipe,
                                     "inv_tranfo.out_file",
                                     pad_gen_5tt, "trans_file")

                    # outputnode
                    seg_pipe.connect(pad_gen_5tt, "out_file",
                                     outputnode, "gen_5tt")

        else:
            seg_pipe.connect(brain_segment_pipe, 'outputnode.gen_5tt',
                             outputnode, 'gen_5tt')

    if "nii_to_mesh_fs_pipe" in params.keys():
        nii_to_mesh_fs_pipe = create_nii_to_mesh_fs_pipe(
            params=parse_key(params, "nii_to_mesh_fs_pipe"))

        seg_pipe.connect(brain_extraction_pipe, 'outputnode.debiased_T1',
                         nii_to_mesh_fs_pipe, 'inputnode.reg_brain_file')

        seg_pipe.connect(brain_segment_pipe,
                         'segment_atropos_pipe.outputnode.threshold_wm',
                         nii_to_mesh_fs_pipe, 'inputnode.wm_mask_file')

        seg_pipe.connect(inputnode, 'indiv_params',
                         nii_to_mesh_fs_pipe, 'inputnode.indiv_params')

    return seg_pipe
