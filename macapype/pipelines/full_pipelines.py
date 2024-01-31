"""
    Gather all full pipelines

"""
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from nipype.interfaces import fsl
from nipype.interfaces import ants

from nipype.interfaces.niftyreg.regutils import RegResample

from ..utils.utils_nodes import NodeParams

from macapype.nodes.correct_bias import T1xT2BiasFieldCorrection
from macapype.nodes.register import IterREGBET

from macapype.nodes.pad import pad_back, apply_to_stereo

from .prepare import (create_short_preparation_pipe,
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

from .register import (create_register_NMT_pipe, create_reg_seg_pipe,
                       create_native_to_stereo_pipe)

from .extract_brain import create_extract_pipe

from .surface import (create_nii_to_mesh_pipe, create_nii_to_mesh_fs_pipe,
                      create_nii2mesh_brain_pipe, create_IsoSurface_brain_pipe)

from macapype.utils.misc import parse_key, list_input_files, show_files

###############################################################################
# SPM based segmentation (from: Régis Trapeau)
# -soft SPM or SPM_T1
###############################################################################


def create_full_spm_subpipes(
        params_template, params_template_aladin,
        params_template_stereo,
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
                                      'native_T1', 'native_T2',
                                      'cropped_to_native_trans',
                                      'debiased_T1', 'masked_debiased_T1',
                                      'debiased_T2', 'masked_debiased_T2',
                                      "wmgm_stl",
                                      'prob_wm', 'prob_gm', 'prob_csf',
                                      'gen_5tt',
                                      'stereo_native_T1', 'stereo_debiased_T1',
                                      'stereo_native_T2', 'stereo_debiased_T2',
                                      'stereo_masked_debiased_T1',
                                      'stereo_masked_debiased_T2',
                                      'stereo_brain_mask',
                                      'stereo_prob_wm', 'stereo_prob_gm',
                                      'stereo_prob_csf',
                                      'stereo_segmented_brain_mask',
                                      'stereo_gen_5tt',
                                      "native_to_stereo_trans"]),
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

    seg_pipe.connect(data_preparation_pipe, 'outputnode.native_T1',
                     outputnode, 'native_T1')

    seg_pipe.connect(data_preparation_pipe, 'outputnode.native_T2',
                     outputnode, 'native_T2')

    if "short_preparation_pipe" in params.keys():
        if "crop_T1" not in params["short_preparation_pipe"].keys():
            seg_pipe.connect(data_preparation_pipe, "inv_tranfo.out_file",
                             outputnode, 'cropped_to_native_trans')

    debias = NodeParams(T1xT2BiasFieldCorrection(),
                        params=parse_key(params, "debias"),
                        name='debias')

    seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                     debias, 't1_file')
    seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T2',
                     debias, 't2_file')
    seg_pipe.connect(inputnode, ('indiv_params', parse_key, "debias"),
                     debias, 'indiv_params')

    debias.inputs.bet = 1

    if pad:
        pad_mask = pad_back(
            seg_pipe, data_preparation_pipe, inputnode,
            debias, "debiased_mask_file",
            outputnode, "brain_mask",  params)

        pad_masked_debiased_T1 = pad_back(
            seg_pipe, data_preparation_pipe, inputnode,
            debias, "t1_debiased_brain_file",
            outputnode, "masked_debiased_T1", params)

        pad_debiased_T1 = pad_back(
            seg_pipe, data_preparation_pipe, inputnode,
            debias, "t1_debiased_file",
            outputnode, "debiased_T1", params)

        pad_masked_debiased_T2 = pad_back(
            seg_pipe, data_preparation_pipe, inputnode,
            debias, "t2_debiased_brain_file",
            outputnode, "masked_debiased_T2", params)

        pad_debiased_T2 = pad_back(
            seg_pipe, data_preparation_pipe, inputnode,
            debias, "t2_debiased_file",
            outputnode, "debiased_T2", params)

    else:
        seg_pipe.connect(debias, "debiased_mask_file",
                         outputnode, "brain_mask")

        seg_pipe.connect(debias, 't1_debiased_brain_file',
                         outputnode, "masked_debiased_T1")

        seg_pipe.connect(debias, 't1_debiased_file',
                         outputnode, "debiased_T1")

        seg_pipe.connect(debias, 't2_debiased_brain_file',
                         outputnode, "masked_debiased_T2")

        seg_pipe.connect(debias, 't2_debiased_file',
                         outputnode, "debiased_T2")

    if "native_to_stereo_pipe" in params.keys():

        native_to_stereo_pipe = create_native_to_stereo_pipe(
            "native_to_stereo_pipe",
            params=parse_key(params, "native_to_stereo_pipe"))

        seg_pipe.connect(native_to_stereo_pipe,
                         'outputnode.native_to_stereo_trans',
                         outputnode, 'native_to_stereo_trans')

        if "skull_stripped_template" in params["native_to_stereo_pipe"]:
            print("Found skull_stripped_template in native_to_stereo_pipe")

            if pad:

                # skull stripped version
                print("using skull_stripped_template for stereotaxic norm")

                if "use_T2" in params["native_to_stereo_pipe"].keys():
                    seg_pipe.connect(pad_masked_debiased_T2, "out_file",
                                     native_to_stereo_pipe,
                                     'inputnode.native_T1')

                    seg_pipe.connect(native_to_stereo_pipe,
                                     'outputnode.stereo_native_T1',
                                     outputnode, "stereo_masked_debiased_T2")

                    apply_to_stereo(
                        seg_pipe, native_to_stereo_pipe,
                        pad_masked_debiased_T1, "out_file",
                        outputnode, "stereo_masked_debiased_T1", )

                    apply_to_stereo(
                        seg_pipe, native_to_stereo_pipe,
                        pad_debiased_T1, "out_file",
                        outputnode, "stereo_debiased_T1")

                    apply_to_stereo(
                        seg_pipe, native_to_stereo_pipe,
                        pad_debiased_T2, "out_file",
                        outputnode, "stereo_debiased_T2")

                else:
                    seg_pipe.connect(pad_masked_debiased_T1, "out_file",
                                     native_to_stereo_pipe,
                                     'inputnode.native_T1')

                    seg_pipe.connect(native_to_stereo_pipe,
                                     'outputnode.stereo_native_T1',
                                     outputnode, "stereo_masked_debiased_T1")

                    apply_to_stereo(
                        seg_pipe, native_to_stereo_pipe,
                        pad_masked_debiased_T2, "out_file",
                        outputnode, "stereo_masked_debiased_T2", )

                    apply_to_stereo(
                        seg_pipe, native_to_stereo_pipe,
                        pad_debiased_T1, "out_file",
                        outputnode, "stereo_debiased_T1")

                    apply_to_stereo(
                        seg_pipe, native_to_stereo_pipe,
                        pad_debiased_T2, "out_file",
                        outputnode, "stereo_debiased_T2")

                native_to_stereo_pipe.inputs.inputnode.stereo_T1 = \
                    params_template_stereo["template_brain"]

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    data_preparation_pipe, "outputnode.native_T1",
                    outputnode, "stereo_native_T1")

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    data_preparation_pipe, "outputnode.native_T2",
                    outputnode, "stereo_native_T2")

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    pad_mask, 'out_file',
                    outputnode, "stereo_brain_mask")

            else:
                # full head version
                seg_pipe.connect(data_preparation_pipe, "outputnode.native_T1",
                                 native_to_stereo_pipe, 'inputnode.native_T1')

                native_to_stereo_pipe.inputs.inputnode.stereo_T1 = \
                    params_template_stereo["template_head"]

                seg_pipe.connect(native_to_stereo_pipe,
                                 "outputnode.stereo_native_T1",
                                 outputnode, "stereo_native_T1")

        else:

            # full head version
            seg_pipe.connect(data_preparation_pipe, "outputnode.native_T1",
                             native_to_stereo_pipe, 'inputnode.native_T1')

            native_to_stereo_pipe.inputs.inputnode.stereo_T1 = \
                params_template_stereo["template_head"]

            seg_pipe.connect(native_to_stereo_pipe,
                             "outputnode.stereo_native_T1",
                             outputnode, "stereo_native_T1")

            apply_to_stereo(
                seg_pipe, native_to_stereo_pipe,
                data_preparation_pipe, "outputnode.native_T2",
                outputnode, "stereo_native_T2")

            if pad:

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    pad_debiased_T1, "out_file",
                    outputnode, "stereo_debiased_T1")

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    pad_debiased_T2, "out_file",
                    outputnode, "stereo_debiased_T2")

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    pad_masked_debiased_T1, "out_file",
                    outputnode, "stereo_masked_debiased_T1")

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    pad_masked_debiased_T2, "out_file",
                    outputnode, "stereo_masked_debiased_T2")

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    pad_mask, "out_file",
                    outputnode, "stereo_brain_mask")

    # Bias correction of cropped images
    if "reg" not in params.keys():

        print("No reg, skipping")
        return seg_pipe

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

        pad_prob_gm = pad_back(
            seg_pipe, data_preparation_pipe, inputnode,
            old_segment_pipe, "outputnode.prob_gm",
            outputnode, "prob_gm", params)

        pad_prob_wm = pad_back(
            seg_pipe, data_preparation_pipe, inputnode,
            old_segment_pipe, "outputnode.prob_wm",
            outputnode, "prob_wm", params)

        pad_prob_csf = pad_back(
            seg_pipe, data_preparation_pipe, inputnode,
            old_segment_pipe, "outputnode.prob_csf",
            outputnode, "prob_csf", params)

        if "native_to_stereo_pipe" in params:

            apply_to_stereo(
                seg_pipe, native_to_stereo_pipe,
                pad_prob_gm, 'out_file',
                outputnode, "stereo_prob_gm")

            apply_to_stereo(
                seg_pipe, native_to_stereo_pipe,
                pad_prob_wm, 'out_file',
                outputnode, "stereo_prob_wm")

            apply_to_stereo(
                seg_pipe, native_to_stereo_pipe,
                pad_prob_csf, 'out_file',
                outputnode, "stereo_prob_csf")

    else:
        seg_pipe.connect(old_segment_pipe, 'outputnode.prob_wm',
                         outputnode, 'prob_wm')

        seg_pipe.connect(old_segment_pipe, 'outputnode.prob_csf',
                         outputnode, 'prob_csf')

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

        seg_pipe.connect(mask_from_seg_pipe, "wmgm2mesh.stl_file",
                         outputnode, 'wmgm_stl')

        # prob_gm
        if pad and space == "native":

            pad_seg_mask = pad_back(
                seg_pipe, data_preparation_pipe, inputnode,
                mask_from_seg_pipe,
                'merge_indexed_mask.indexed_mask',
                outputnode, "segmented_brain_mask", params)

            if "native_to_stereo_pipe" in params:

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    pad_seg_mask, 'out_file',
                    outputnode, "stereo_segmented_brain_mask")

        else:
            seg_pipe.connect(
                mask_from_seg_pipe,
                'merge_indexed_mask.indexed_mask',
                outputnode, 'stereo_segmented_brain_mask')

    # LEGACY
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

    if "export_5tt_pipe" in params["old_segment_pipe"].keys():

        export_5tt_pipe = create_5tt_pipe(
            params=parse_key(params["old_segment_pipe"], "export_5tt_pipe"))

        seg_pipe.connect(
            old_segment_pipe, 'outputnode.threshold_csf',
            export_5tt_pipe, 'inputnode.gm_file')

        seg_pipe.connect(
            old_segment_pipe, 'outputnode.threshold_csf',
            export_5tt_pipe, 'inputnode.wm_file')

        seg_pipe.connect(
            old_segment_pipe, 'outputnode.threshold_csf',
            export_5tt_pipe, 'inputnode.csf_file')

        if pad and space == "native":

            pad_gen_5tt = pad_back(
                seg_pipe, data_preparation_pipe, inputnode,
                export_5tt_pipe, 'export_5tt.gen_5tt_file',
                outputnode, "gen_5tt", params)

            if "native_to_stereo_pipe" in params:

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    pad_gen_5tt, 'out_file',
                    outputnode, "stereo_gen_5tt")
        else:

            seg_pipe.connect(
                export_5tt_pipe, 'export_5tt.gen_5tt_file',
                outputnode, 'gen_5tt')

    return seg_pipe

###############################################################################
# ANTS based segmentation (from Kepkee Loh / Julien Sein)
# (-soft ANTS)
###############################################################################


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
            fields=['masked_debiased_T1', "debiased_T1", 'indiv_params']),
        name='inputnode')

    # creating outputnode
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["segmented_file", "threshold_gm", "threshold_wm",
                    "threshold_csf", "prob_gm", "prob_wm",
                    "prob_csf", "gen_5tt"]),
        name='outputnode')

    if "register_NMT_pipe" in params:

        # register NMT template, template mask and priors to subject T1
        register_NMT_pipe = create_register_NMT_pipe(
            params_template=params_template,
            params=parse_key(params, "register_NMT_pipe"))

        brain_segment_pipe.connect(
            inputnode, 'masked_debiased_T1',
            register_NMT_pipe, "inputnode.T1")

        brain_segment_pipe.connect(
            inputnode, 'indiv_params',
            register_NMT_pipe, "inputnode.indiv_params")

    elif "reg" in params:
        # Iterative registration to the INIA19 template
        reg = NodeParams(
            IterREGBET(),
            params=parse_key(params, "reg"),
            name='reg')

        reg.inputs.refb_file = params_template["template_brain"]

        brain_segment_pipe.connect(
            inputnode, 'debiased_T1',
            reg, 'inw_file')

        brain_segment_pipe.connect(
            inputnode, 'masked_debiased_T1',
            reg, 'inb_file')

        brain_segment_pipe.connect(
            inputnode, ('indiv_params', parse_key, "reg"),
            reg, 'indiv_params')

        if "template_seg" in params_template.keys():

            # seg
            register_seg_to_nat = pe.Node(
                fsl.ApplyXFM(), name="register_seg_to_nat")
            register_seg_to_nat.inputs.interp = "nearestneighbour"

            register_seg_to_nat.inputs.in_file = params_template[
                "template_seg"]
            brain_segment_pipe.connect(
                inputnode, 'masked_debiased_T1',
                register_seg_to_nat, 'reference')

            brain_segment_pipe.connect(
                reg, 'inv_transfo_file',
                register_seg_to_nat, "in_matrix_file")

        else:
            # gm
            register_gm_to_nat = pe.Node(
                fsl.ApplyXFM(), name="register_gm_to_nat")
            register_gm_to_nat.inputs.output_type = "NIFTI"  # for SPM segment
            register_gm_to_nat.inputs.interp = "nearestneighbour"

            register_gm_to_nat.inputs.in_file = params_template["template_gm"]

            brain_segment_pipe.connect(
                inputnode, 'masked_debiased_T1',
                register_gm_to_nat, 'reference')

            brain_segment_pipe.connect(
                inputnode, 'inv_transfo_file',
                register_gm_to_nat, "in_matrix_file")

            # wm
            register_wm_to_nat = pe.Node(
                fsl.ApplyXFM(), name="register_wm_to_nat")
            register_wm_to_nat.inputs.output_type = "NIFTI"  # for SPM segment
            register_wm_to_nat.inputs.interp = "nearestneighbour"

            register_wm_to_nat.inputs.in_file = params_template["template_wm"]

            brain_segment_pipe.connect(
                inputnode, 'masked_debiased_T1',
                register_wm_to_nat, 'reference')

            brain_segment_pipe.connect(
                inputnode, 'inv_transfo_file',
                register_wm_to_nat, "in_matrix_file")

            # csf
            register_csf_to_nat = pe.Node(
                fsl.ApplyXFM(), name="register_csf_to_nat")
            register_csf_to_nat.inputs.output_type = "NIFTI"  # for SPM segment
            register_csf_to_nat.inputs.interp = "nearestneighbour"

            register_csf_to_nat.inputs.in_file = params_template[
                "template_csf"]

            brain_segment_pipe.connect(
                inputnode, 'masked_debiased_T1',
                register_csf_to_nat, 'reference')

            brain_segment_pipe.connect(
                inputnode, 'inv_transfo_file',
                register_csf_to_nat, "in_matrix_file")
    else:
        print("##### Error, no coregistration method is defined")
        return brain_segment_pipe

    # ants Atropos
    if "template_seg" in params_template.keys():

        print("#### create_segment_atropos_seg_pipe ")
        segment_atropos_pipe = create_segment_atropos_seg_pipe(
            params=parse_key(params, "segment_atropos_pipe"))

        if "register_NMT_pipe" in params:
            brain_segment_pipe.connect(
                register_NMT_pipe, 'outputnode.native_template_seg',
                segment_atropos_pipe, "inputnode.seg_file")
        elif "reg" in params:
            brain_segment_pipe.connect(
                register_seg_to_nat, 'out_file',
                segment_atropos_pipe, "inputnode.seg_file")
    else:
        print("#### create_segment_atropos_pipe (3 tissues) ")

        segment_atropos_pipe = create_segment_atropos_pipe(
            params=parse_key(params, "segment_atropos_pipe"))

        # linking priors if "use_priors" in params
        if "use_priors" in params["segment_atropos_pipe"].keys():

            if "register_NMT_pipe" in params:
                brain_segment_pipe.connect(
                    register_NMT_pipe, 'outputnode.native_template_csf',
                    segment_atropos_pipe, "inputnode.csf_prior_file")
                brain_segment_pipe.connect(
                    register_NMT_pipe,  'outputnode.native_template_gm',
                    segment_atropos_pipe, "inputnode.gm_prior_file")
                brain_segment_pipe.connect(
                    register_NMT_pipe,  'outputnode.native_template_wm',
                    segment_atropos_pipe, "inputnode.wm_prior_file")
            elif "reg" in params:

                print("To be validated...")
                brain_segment_pipe.connect(
                    register_csf_to_nat, "out_file",
                    segment_atropos_pipe, "inputnode.csf_prior_file")
                brain_segment_pipe.connect(
                    register_gm_to_nat, "out_file",
                    segment_atropos_pipe, "inputnode.gm_prior_file")
                brain_segment_pipe.connect(
                    register_gm_to_nat, "out_file",
                    segment_atropos_pipe, "inputnode.wm_prior_file")

    # input to segment_atropos_pipe
    brain_segment_pipe.connect(
        inputnode, 'masked_debiased_T1',
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
        if "reg" in params:
            brain_segment_pipe.connect(
                reg, 'transfo_file',
                reg_seg_pipe, 'inputnode.transfo_file')

        elif "register_NMT_pipe" in params:
            brain_segment_pipe.connect(
                register_NMT_pipe,
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

# #############################################################################################################################


def create_full_ants_subpipes(
        params_template, params_template_aladin, params_template_stereo,
        params={}, name="full_ants_subpipes", mask_file=None,
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
                    'prob_csf', "gen_5tt",
                    "masked_debiased_T1", "debiased_T1",
                    "masked_debiased_T2", "debiased_T2",
                    "cropped_brain_mask", "cropped_debiased_T1",
                    "native_T1", "native_T2", "cropped_to_native_trans",
                    "wmgm_stl", "wmgm_mask",
                    'stereo_native_T1', 'stereo_debiased_T1',
                    'stereo_masked_debiased_T1',
                    'stereo_native_T2', 'stereo_debiased_T2',
                    'stereo_masked_debiased_T2',
                    'stereo_brain_mask', 'stereo_segmented_brain_mask',
                    'stereo_prob_gm', 'stereo_prob_wm', 'stereo_prob_csf',
                    "stereo_wmgm_mask", "stereo_wmgm_stl",
                    "native_to_stereo_trans"]),
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

    seg_pipe.connect(data_preparation_pipe, 'outputnode.native_T1',
                     outputnode, 'native_T1')

    seg_pipe.connect(data_preparation_pipe, 'outputnode.native_T2',
                     outputnode, 'native_T2')

    seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                     outputnode, "cropped_debiased_T1")

    if "short_preparation_pipe" in params.keys():
        if "crop_T1" not in params["short_preparation_pipe"].keys():
            seg_pipe.connect(data_preparation_pipe, "inv_tranfo.out_file",
                             outputnode, 'cropped_to_native_trans')

    # ######################################## correct bias
    assert not ("fast" in params.keys() and "N4debias" in
                params.keys()), "error, only one of correct_bias_pipe\
                or N4debias should be present"

    if "correct_bias_pipe" in params.keys():

        print("Found create_correct_bias_pipe in params.json")

        # Correct_bias_T1_T2
        correct_bias_pipe = create_correct_bias_pipe(
            params=parse_key(params, "correct_bias_pipe"))

        seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                         correct_bias_pipe, 'inputnode.preproc_T1')

        seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T2',
                         correct_bias_pipe, 'inputnode.preproc_T2')

        if pad:

            pad_debiased_T1 = pad_back(
                seg_pipe, data_preparation_pipe, inputnode,
                correct_bias_pipe, "outputnode.debiased_T1",
                outputnode, "debiased_T1", params)

            pad_debiased_T2 = pad_back(
                seg_pipe, data_preparation_pipe, inputnode,
                correct_bias_pipe, "outputnode.debiased_T2",
                outputnode, "debiased_T2", params)

        else:
            seg_pipe.connect(correct_bias_pipe,
                             "outputnode.debiased_T1",
                             outputnode, "debiased_T1")

            seg_pipe.connect(correct_bias_pipe,
                             "outputnode.debiased_T2",
                             outputnode, "debiased_T2")

    elif "N4debias" in params.keys():
        print("Found N4debias in params.json")

        # N4 intensity normalization over T1
        N4debias_T1 = NodeParams(ants.N4BiasFieldCorrection(),
                                 params=parse_key(params, "N4debias"),
                                 name='N4debias_T1')

        seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                         N4debias_T1, "input_image")

        seg_pipe.connect(
            inputnode, ('indiv_params', parse_key, "N4debias"),
            N4debias_T1, "indiv_params")

        # N4 intensity normalization over T2
        N4debias_T2 = NodeParams(ants.N4BiasFieldCorrection(),
                                 params=parse_key(params, "N4debias"),
                                 name='N4debias_T2')

        seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T2',
                         N4debias_T2, "input_image")

        seg_pipe.connect(
            inputnode, ('indiv_params', parse_key, "N4debias"),
            N4debias_T2, "indiv_params")

        if pad:

            pad_debiased_T1 = pad_back(
                seg_pipe, data_preparation_pipe, inputnode,
                N4debias_T1, "output_image",
                outputnode, "debiased_T1", params)

            pad_debiased_T2 = pad_back(
                seg_pipe, data_preparation_pipe, inputnode,
                N4debias_T2, "output_image",
                outputnode, "debiased_T2", params)

        else:
            seg_pipe.connect(N4debias_T1, "output_image",
                             outputnode, "debiased_T1")

            seg_pipe.connect(N4debias_T2, "output_image",
                             outputnode, "debiased_T2")

    elif "fast" in params.keys():

        print("Found fast in params.json")

        # fast over T1
        fast_T1 = NodeParams(
            fsl.FAST(),
            params=parse_key(params, "fast"),
            name='fast_T1')

        fast_T1.inputs.output_biascorrected = True
        fast_T1.inputs.output_biasfield = True

        seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                         fast_T1, "in_files")

        seg_pipe.connect(
            inputnode, ('indiv_params', parse_key, "fast"),
            fast_T1, "indiv_params")

        # fast over T2
        fast_T2 = NodeParams(
            fsl.FAST(),
            params=parse_key(params, "fast"),
            name='fast_T2')

        fast_T2.inputs.output_biascorrected = True
        fast_T2.inputs.output_biasfield = True

        seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T2',
                         fast_T2, "in_files")

        seg_pipe.connect(
            inputnode, ('indiv_params', parse_key, "fast"),
            fast_T2, "indiv_params")

        if pad:

            pad_debiased_T1 = pad_back(
                seg_pipe, data_preparation_pipe, inputnode,
                fast_T1, "restored_image",
                outputnode, "debiased_T1", params)

            pad_debiased_T2 = pad_back(
                seg_pipe, data_preparation_pipe, inputnode,
                fast_T2, "restored_image",
                outputnode, "debiased_T2", params)

        else:
            seg_pipe.connect(fast_T1, "restored_image",
                             outputnode, "debiased_T1")

            seg_pipe.connect(fast_T2, "restored_image",
                             outputnode, "debiased_T2")

    else:
        print("No debias will be performed before extract_pipe")

    # #### stereo to native
    if "native_to_stereo_pipe" in params.keys():
        if "skull_stripped_template" not in params["native_to_stereo_pipe"]:

            native_to_stereo_pipe = create_native_to_stereo_pipe(
                "native_to_stereo_pipe",
                params=parse_key(params, "native_to_stereo_pipe"))

            seg_pipe.connect(native_to_stereo_pipe,
                             'outputnode.native_to_stereo_trans',
                             outputnode, 'native_to_stereo_trans')

            # full head version
            seg_pipe.connect(data_preparation_pipe, "outputnode.native_T1",
                             native_to_stereo_pipe, 'inputnode.native_T1')

            native_to_stereo_pipe.inputs.inputnode.stereo_T1 = \
                params_template_stereo["template_head"]

            seg_pipe.connect(native_to_stereo_pipe,
                             "outputnode.stereo_native_T1",
                             outputnode, "stereo_native_T1")

            apply_to_stereo(
                seg_pipe, native_to_stereo_pipe,
                data_preparation_pipe, "outputnode.native_T2",
                outputnode, "stereo_native_T2")

            if pad:
                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    pad_debiased_T2, "out_file",
                    outputnode, "stereo_debiased_T2")

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    pad_debiased_T1, "out_file",
                    outputnode, "stereo_debiased_T1")

    # ################# extract mask
    if mask_file is None:

        # full extract brain pipeline (correct_bias, denoising, extract brain)
        if "extract_pipe" not in params.keys():
            return seg_pipe

        # brain extraction
        extract_pipe = create_extract_pipe(
            params_template=params_template,
            params=parse_key(params, "extract_pipe"))

        seg_pipe.connect(inputnode, "indiv_params",
                                    extract_pipe, "inputnode.indiv_params")

        seg_pipe.connect(extract_pipe, "smooth_mask.out_file",
                         outputnode, "cropped_brain_mask")

        if "correct_bias_pipe" in params:
            seg_pipe.connect(correct_bias_pipe,
                             "outputnode.debiased_T1",
                             extract_pipe, "inputnode.restore_T1")

        elif "N4debias" in params.keys():
            # brain extraction
            seg_pipe.connect(N4debias_T1, "output_image",
                             extract_pipe, "inputnode.restore_T1")

        elif "fast" in params.keys():

            # brain extraction
            seg_pipe.connect(fast_T1, ("restored_image", show_files),
                             extract_pipe, "inputnode.restore_T1")
        else:

            seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                             extract_pipe, "inputnode.restore_T1")

        if pad:
            pad_mask = pad_back(
                seg_pipe, data_preparation_pipe, inputnode,
                extract_pipe, "smooth_mask.out_file",
                outputnode, "brain_mask", params)
        else:
            seg_pipe.connect(extract_pipe, "smooth_mask.out_file",
                             outputnode, "brain_mask")

    else:

        outputnode.inputs.brain_mask = mask_file

    # ################################################ masked_debias ##
    # correcting for bias T1/T2, but this time with a mask
    if "masked_correct_bias_pipe" in params.keys():
        masked_correct_bias_pipe = create_masked_correct_bias_pipe(
            params=parse_key(params, "masked_correct_bias_pipe"))

        if "correct_bias_pipe" in params.keys():

            seg_pipe.connect(correct_bias_pipe, "outputnode.debiased_T1",
                             masked_correct_bias_pipe, "inputnode.preproc_T1")

            seg_pipe.connect(correct_bias_pipe, "outputnode.debiased_T2",
                             masked_correct_bias_pipe, "inputnode.preproc_T2")

        elif "N4debias" in params.keys():

            seg_pipe.connect(N4debias_T1, "output_image",
                             masked_correct_bias_pipe, "inputnode.preproc_T1")

            seg_pipe.connect(N4debias_T2, "output_image",
                             masked_correct_bias_pipe, "inputnode.preproc_T2")

        elif "fast" in params.keys():

            seg_pipe.connect(fast_T1, ("restored_image", show_files),
                             masked_correct_bias_pipe, "inputnode.preproc_T1")

            seg_pipe.connect(fast_T2, ("restored_image", show_files),
                             masked_correct_bias_pipe, "inputnode.preproc_T2")

        else:

            seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                             masked_correct_bias_pipe, "inputnode.preproc_T1")

            seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T2',
                             masked_correct_bias_pipe, "inputnode.preproc_T2")

        seg_pipe.connect(extract_pipe, "smooth_mask.out_file",
                         masked_correct_bias_pipe, "inputnode.brain_mask")

        if pad:

            pad_masked_debiased_T1 = pad_back(
                seg_pipe, data_preparation_pipe, inputnode,
                masked_correct_bias_pipe,
                'outputnode.mask_debiased_T1',
                outputnode, "masked_debiased_T1", params)

            pad_masked_debiased_T2 = pad_back(
                seg_pipe, data_preparation_pipe, inputnode,
                masked_correct_bias_pipe,
                'outputnode.mask_debiased_T2',
                outputnode, "masked_debiased_T2", params)

        else:

            # outputnode
            seg_pipe.connect(masked_correct_bias_pipe,
                             'outputnode.mask_debiased_T1',
                             outputnode, "masked_debiased_T1")

            seg_pipe.connect(masked_correct_bias_pipe,
                             'outputnode.mask_debiased_T2',
                             outputnode, "masked_debiased_T2")

    elif "debias" in params.keys():
        # Bias correction of cropped images
        debias = NodeParams(T1xT2BiasFieldCorrection(),
                            params=parse_key(params, "debias"),
                            name='debias')

        if "N4debias" in params.keys():

            seg_pipe.connect(N4debias_T1, "output_image",
                             debias, 't1_file')

            seg_pipe.connect(N4debias_T2, "output_image",
                             debias, 't2_file')

        elif "fast" in params.keys():

            seg_pipe.connect(fast_T1, ("restored_image", show_files),
                             debias, 't1_file')

            seg_pipe.connect(fast_T2, ("restored_image", show_files),
                             debias, 't2_file')

        else:

            seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                             debias, 't1_file')

            seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T2',
                             debias, 't2_file')

        seg_pipe.connect(extract_pipe, "smooth_mask.out_file",
                         debias, 'b')

        # TODO is not used now...
        seg_pipe.connect(
            inputnode, ('indiv_params', parse_key, "debias"),
            debias, 'indiv_params')

        # padding
        if pad:
            pad_masked_debiased_T1 = pad_back(
                seg_pipe, data_preparation_pipe, inputnode,
                debias, 't1_debiased_brain_file',
                outputnode, "masked_debiased_T1", params)

            pad_masked_debiased_T2 = pad_back(
                seg_pipe, data_preparation_pipe, inputnode,
                debias, 't2_debiased_brain_file',
                outputnode, "masked_debiased_T2", params)

        else:

            seg_pipe.connect(debias, 't1_debiased_brain_file',
                             outputnode, "masked_debiased_T1")

            seg_pipe.connect(debias, 't2_debiased_brain_file',
                             outputnode, "masked_debiased_T2")
    else:

        print("**** Error, masked_correct_bias_pipe or debias \
            should be in brain_extraction_pipe of params.json")
        print("No T1*T2 debias will be performed")

        # restore_mask_T1
        restore_mask_T1 = pe.Node(fsl.ApplyMask(), name='restore_mask_T1')

        # restore_mask_T2
        restore_mask_T2 = pe.Node(fsl.ApplyMask(), name='restore_mask_T2')

        if "N4debias" in params.keys():

            seg_pipe.connect(N4debias_T1, "output_image",
                             restore_mask_T1, 'in_file')

            seg_pipe.connect(N4debias_T2, "output_image",
                             restore_mask_T2, 'in_file')

        elif "fast" in params.keys():

            seg_pipe.connect(fast_T1, ("restored_image", show_files),
                             restore_mask_T1, 'in_file')

            seg_pipe.connect(fast_T2, ("restored_image", show_files),
                             restore_mask_T2, 'in_file')

        else:

            seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                             restore_mask_T1, 'in_file')

            seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T2',
                             restore_mask_T2, 'in_file')

        seg_pipe.connect(extract_pipe, "smooth_mask.out_file",
                         restore_mask_T1, 'mask_file')

        seg_pipe.connect(extract_pipe, "smooth_mask.out_file",
                         restore_mask_T2, 'mask_file')

        if pad:

            pad_masked_debiased_T1 = pad_back(
                seg_pipe, data_preparation_pipe, inputnode,
                restore_mask_T1, 'out_file',
                outputnode, "masked_debiased_T1", params)

            pad_masked_debiased_T2 = pad_back(
                seg_pipe, data_preparation_pipe, inputnode,
                restore_mask_T2, 'out_file',
                outputnode, "masked_debiased_T2", params)

        else:
            # outputnode
            seg_pipe.connect(restore_mask_T1, 'out_file',
                             outputnode, "masked_debiased_T1")

            seg_pipe.connect(restore_mask_T2, 'out_file',
                             outputnode, "masked_debiased_T2")

    # #### stereo to native
    if "native_to_stereo_pipe" in params.keys():

        if "skull_stripped_template" in params["native_to_stereo_pipe"]:

            native_to_stereo_pipe = create_native_to_stereo_pipe(
                "native_to_stereo_pipe",
                params=parse_key(params, "native_to_stereo_pipe"))

            seg_pipe.connect(native_to_stereo_pipe,
                             'outputnode.native_to_stereo_trans',
                             outputnode, 'native_to_stereo_trans')

            print("Found skull_stripped_template in native_to_stereo_pipe")

            if pad:

                # skull stripped version
                print("using skull_stripped_template for stereotaxic norm")

                if "use_T2" in params["native_to_stereo_pipe"].keys():
                    seg_pipe.connect(pad_masked_debiased_T2, "out_file",
                                     native_to_stereo_pipe,
                                     'inputnode.native_T1')

                    seg_pipe.connect(native_to_stereo_pipe,
                                     'outputnode.stereo_native_T1',
                                     outputnode, "stereo_masked_debiased_T2")

                    apply_to_stereo(
                        seg_pipe, native_to_stereo_pipe,
                        pad_masked_debiased_T1, "out_file",
                        outputnode, "stereo_masked_debiased_T1")

                else:
                    seg_pipe.connect(pad_masked_debiased_T1, "out_file",
                                     native_to_stereo_pipe,
                                     'inputnode.native_T1')

                    seg_pipe.connect(native_to_stereo_pipe,
                                     'outputnode.stereo_native_T1',
                                     outputnode, "stereo_masked_debiased_T1")

                    apply_to_stereo(
                        seg_pipe, native_to_stereo_pipe,
                        pad_masked_debiased_T2, "out_file",
                        outputnode, "stereo_masked_debiased_T2")

                native_to_stereo_pipe.inputs.inputnode.stereo_T1 = \
                    params_template_stereo["template_brain"]

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    data_preparation_pipe, "outputnode.native_T1",
                    outputnode, "stereo_native_T1")

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    data_preparation_pipe, "outputnode.native_T2",
                    outputnode, "stereo_native_T2")

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    pad_debiased_T1, 'out_file',
                    outputnode, "stereo_debiased_T1")

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    pad_debiased_T2, 'out_file',
                    outputnode, "stereo_debiased_T2")

            else:
                # full head version
                seg_pipe.connect(data_preparation_pipe, "outputnode.native_T1",
                                 native_to_stereo_pipe, 'inputnode.native_T1')

                native_to_stereo_pipe.inputs.inputnode.stereo_T1 = \
                    params_template_stereo["template_head"]

                seg_pipe.connect(native_to_stereo_pipe,
                                 "outputnode.stereo_native_T1",
                                 outputnode, "stereo_native_T1")

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    data_preparation_pipe, "outputnode.native_T2",
                    outputnode, "stereo_native_T2")

        else:
            # remaining applies if not skull_stripped_template
            if pad:

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    pad_masked_debiased_T1, 'out_file',
                    outputnode, "stereo_masked_debiased_T1")

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    pad_masked_debiased_T2, 'out_file',
                    outputnode, "stereo_masked_debiased_T2")

        if "extract_pipe" in params.keys() and pad:
            apply_to_stereo(
                seg_pipe, native_to_stereo_pipe,
                pad_mask, 'out_file',
                outputnode, "stereo_brain_mask")

    # ################################### brain_segment
    # (restarting from the avg_align files)
    if "brain_segment_pipe" not in params.keys():
        return seg_pipe

    brain_segment_pipe = create_brain_segment_from_mask_pipe(
        params_template=params_template,
        params=parse_key(params, "brain_segment_pipe"), space=space)

    seg_pipe.connect(inputnode, 'indiv_params',
                     brain_segment_pipe, 'inputnode.indiv_params')

    if mask_file is None:

        if "masked_correct_bias_pipe" in params.keys():
            seg_pipe.connect(
                masked_correct_bias_pipe, 'outputnode.mask_debiased_T1',
                brain_segment_pipe, 'inputnode.masked_debiased_T1')

            if "correct_bias_pipe" in params.keys():
                seg_pipe.connect(
                    correct_bias_pipe, "outputnode.debiased_T1",
                    brain_segment_pipe, 'inputnode.debiased_T1')

            elif "N4debias" in params.keys():
                seg_pipe.connect(
                    N4debias_T1, "output_image",
                    brain_segment_pipe, 'inputnode.debiased_T1')

            elif "fast" in params.keys():
                seg_pipe.connect(
                    fast_T1, ("restored_image", show_files),
                    brain_segment_pipe, 'inputnode.debiased_T1')

            else:
                seg_pipe.connect(
                    data_preparation_pipe, 'outputnode.preproc_T1',
                    brain_segment_pipe, 'inputnode.debiased_T1')

        elif "debias" in params.keys():
            seg_pipe.connect(
                debias, 't1_debiased_brain_file',
                brain_segment_pipe, 'inputnode.masked_debiased_T1')

            seg_pipe.connect(
                debias, 't1_debiased_file',
                brain_segment_pipe, 'inputnode.debiased_T1')

        else:
            seg_pipe.connect(
                restore_mask_T1, 'out_file',
                brain_segment_pipe, 'inputnode.masked_debiased_T1')

    else:

        # apply transfo to list
        apply_crop_external_mask = pe.Node(RegResample(inter_val="NN"),
                                           name='apply_crop_external_mask')

        apply_crop_external_mask.inputs.flo_file = mask_file

        seg_pipe.connect(data_preparation_pipe,
                         'crop_aladin_T1.aff_file',
                         apply_crop_external_mask, "trans_file")

        seg_pipe.connect(data_preparation_pipe, "outputnode.preproc_T1",
                         apply_crop_external_mask, "ref_file")

        # debias T1 and T2 by fast (default)
        # fast over T1
        fast_T1 = pe.Node(
            fsl.FAST(),
            name='fast_T1')

        fast_T1.inputs.output_biascorrected = True
        fast_T1.inputs.output_biasfield = True

        seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                         fast_T1, "in_files")

        seg_pipe.connect(fast_T1, "restored_image",
                         outputnode, "debiased_T1")
        # fast over T2
        fast_T2 = pe.Node(
            fsl.FAST(),
            name='fast_T2')

        fast_T2.inputs.output_biascorrected = True
        fast_T2.inputs.output_biasfield = True

        seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T2',
                         fast_T2, "in_files")

        seg_pipe.connect(fast_T2, "restored_image",
                         outputnode, "debiased_T2")

        # input to brain_segment_pipe
        seg_pipe.connect(apply_crop_external_mask, "out_file",
                         brain_segment_pipe, "inputnode.brain_mask")

        seg_pipe.connect(fast_T1, "restored_image",
                         brain_segment_pipe, 'inputnode.preproc_T1')

        seg_pipe.connect(fast_T2, "restored_image",
                         brain_segment_pipe, 'inputnode.preproc_T2')

        # if in the same space a crop
        # brain_segment_pipe.inputs.inputnode.brain_mask = mask_file

    if pad and space == "native":
        pad_seg_mask = pad_back(
            seg_pipe, data_preparation_pipe, inputnode,
            brain_segment_pipe, "outputnode.segmented_file",
            outputnode, "segmented_brain_mask", params)

        pad_prob_gm = pad_back(
            seg_pipe, data_preparation_pipe, inputnode,
            brain_segment_pipe, "outputnode.prob_gm",
            outputnode, "prob_gm", params)

        pad_prob_wm = pad_back(
            seg_pipe, data_preparation_pipe, inputnode,
            brain_segment_pipe, "outputnode.prob_wm",
            outputnode, "prob_wm", params)

        pad_prob_csf = pad_back(
            seg_pipe, data_preparation_pipe, inputnode,
            brain_segment_pipe, "outputnode.prob_csf",
            outputnode, "prob_csf", params)

    else:
        seg_pipe.connect(brain_segment_pipe, 'outputnode.segmented_file',
                         outputnode, 'segmented_brain_mask')

        seg_pipe.connect(brain_segment_pipe, 'outputnode.prob_gm',
                         outputnode, 'prob_gm')

        seg_pipe.connect(brain_segment_pipe, 'outputnode.prob_wm',
                         outputnode, 'prob_wm')

        seg_pipe.connect(brain_segment_pipe, 'outputnode.prob_csf',
                         outputnode, 'prob_csf')

    # ############################################## export 5tt

    if "export_5tt_pipe" in params["brain_segment_pipe"]:
        if pad and space == "native":
            pad_back(
                seg_pipe, data_preparation_pipe, inputnode,
                brain_segment_pipe, "outputnode.gen_5tt",
                outputnode, "gen_5tt", params)

        else:
            seg_pipe.connect(brain_segment_pipe, 'outputnode.gen_5tt',
                             outputnode, 'gen_5tt')

    if "native_to_stereo_pipe" in params.keys() and pad:

        apply_to_stereo(
                seg_pipe, native_to_stereo_pipe,
                pad_prob_gm, 'out_file',
                outputnode, "stereo_prob_gm")

        apply_to_stereo(
                seg_pipe, native_to_stereo_pipe,
                pad_prob_wm, 'out_file',
                outputnode, "stereo_prob_wm")

        apply_to_stereo(
                seg_pipe, native_to_stereo_pipe,
                pad_prob_csf, 'out_file',
                outputnode, "stereo_prob_csf")

        apply_stereo_seg_mask = apply_to_stereo(
                seg_pipe, native_to_stereo_pipe,
                pad_seg_mask, 'out_file',
                outputnode, "stereo_segmented_brain_mask")

    if "nii2mesh_brain_pipe" in params["brain_segment_pipe"].keys():

        nii2mesh_brain_pipe = create_nii2mesh_brain_pipe(
            params=parse_key(params["brain_segment_pipe"],
                             "nii2mesh_brain_pipe"))

        if pad:
            if "native_to_stereo_pipe" in params.keys():

                seg_pipe.connect(apply_stereo_seg_mask, "out_file",
                                 nii2mesh_brain_pipe,
                                 'inputnode.segmented_file')

                seg_pipe.connect(nii2mesh_brain_pipe, "outputnode.wmgm_stl",
                                 outputnode, 'stereo_wmgm_stl')

                seg_pipe.connect(nii2mesh_brain_pipe, "outputnode.wmgm_nii",
                                 outputnode, 'stereo_wmgm_mask')

            elif space == "native":
                seg_pipe.connect(pad_seg_mask, "out_file",
                                 nii2mesh_brain_pipe,
                                 'inputnode.segmented_file')
        else:
            seg_pipe.connect(brain_segment_pipe, "outputnode.segmented_file",
                             nii2mesh_brain_pipe, 'inputnode.segmented_file')

        seg_pipe.connect(nii2mesh_brain_pipe, "outputnode.wmgm_stl",
                         outputnode, 'wmgm_stl')

        seg_pipe.connect(nii2mesh_brain_pipe, "outputnode.wmgm_nii",
                         outputnode, 'wmgm_mask')
    elif "IsoSurface_brain_pipe" in params.keys():

        IsoSurface_brain_pipe = create_IsoSurface_brain_pipe(
            params=parse_key(params["brain_segment_pipe"],
                             "IsoSurface_brain_pipe"))

        if pad:
            if "native_to_stereo_pipe" in params.keys():

                seg_pipe.connect(apply_stereo_seg_mask, "out_file",
                                 IsoSurface_brain_pipe,
                                 'inputnode.segmented_file')

                seg_pipe.connect(IsoSurface_brain_pipe, "outputnode.wmgm_stl",
                                 outputnode, 'stereo_wmgm_stl')

                seg_pipe.connect(IsoSurface_brain_pipe, "outputnode.wmgm_nii",
                                 outputnode, 'stereo_wmgm_mask')

            elif space == "native":
                seg_pipe.connect(pad_seg_mask, "out_file",
                                 IsoSurface_brain_pipe,
                                 'inputnode.segmented_file')
        else:
            seg_pipe.connect(brain_segment_pipe, "outputnode.segmented_file",
                             IsoSurface_brain_pipe, 'inputnode.segmented_file')

        seg_pipe.connect(IsoSurface_brain_pipe, "outputnode.wmgm_stl",
                         outputnode, 'wmgm_stl')

        seg_pipe.connect(IsoSurface_brain_pipe, "outputnode.wmgm_nii",
                         outputnode, 'wmgm_mask')

    elif 'nii_to_mesh_pipe' in params.keys():
        # kept for compatibility but nii2mesh is prefered...
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

    return seg_pipe


###############################################################################
# ANTS based segmentation for adrien baboons (T1 without T2)
# -soft ANTS_T1


def create_full_T1_ants_subpipes(params_template, params_template_aladin,
                                 params_template_stereo,
                                 params={}, name="full_T1_ants_subpipes",
                                 space="native", pad=False):
    """
    Description: Full pipeline to segment T1 (with no T2).

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
                    'prob_csf', "gen_5tt", "debiased_T1",
                    "masked_debiased_T1", "cropped_brain_mask",
                    "cropped_debiased_T1", "native_T1",
                    "cropped_to_native_trans",
                    "wmgm_stl", "wmgm_mask",
                    'stereo_native_T1', 'stereo_debiased_T1',
                    'stereo_brain_mask', 'stereo_segmented_brain_mask',
                    'stereo_prob_gm', 'stereo_prob_wm',
                    'stereo_prob_csf',
                    "stereo_wmgm_mask", "stereo_wmgm_stl",
                    "native_to_stereo_trans"]),
        name='outputnode')

    # preprocessing (perform preparation pipe with only T1)
    if 'short_preparation_pipe' in params.keys():
        data_preparation_pipe = create_short_preparation_T1_pipe(
            params=parse_key(params, "short_preparation_pipe"),
            params_template=params_template_aladin)

    else:
        print("Error, short_preparation_pipe was not found in params, \
            skipping")
        return seg_pipe

    seg_pipe.connect(inputnode, 'list_T1',
                     data_preparation_pipe, 'inputnode.list_T1')
    seg_pipe.connect(inputnode, 'indiv_params',
                     data_preparation_pipe, 'inputnode.indiv_params')

    # outputnode
    seg_pipe.connect(data_preparation_pipe, 'outputnode.native_T1',
                     outputnode, 'native_T1')

    if "short_preparation_pipe" in params.keys():
        if "crop_T1" not in params["short_preparation_pipe"].keys():
            seg_pipe.connect(data_preparation_pipe, "inv_tranfo.out_file",
                             outputnode, 'cropped_to_native_trans')

    # ######### correct_bias
    if "N4debias" in params.keys():

        print("Found N4debias in params.json")

        # N4 intensity normalization over T1
        N4debias_T1 = NodeParams(ants.N4BiasFieldCorrection(),
                                 params=parse_key(params, "N4debias"),
                                 name='N4debias_T1')

        seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                         N4debias_T1, "input_image")

        seg_pipe.connect(
            inputnode, ('indiv_params', parse_key, "N4debias"),
            N4debias_T1, "indiv_params")

        # outputnode
        if pad and space == "native":
            pad_debiased_T1 = pad_back(
                seg_pipe, data_preparation_pipe, inputnode,
                N4debias_T1, "output_image",
                outputnode, "debiased_T1", params)

        else:

            seg_pipe.connect(N4debias_T1, "output_image",
                             outputnode, "debiased_T1")

    elif "fast" in params.keys():

        print("Found fast in params.json")

        # fast over T1
        fast_T1 = NodeParams(
            fsl.FAST(),
            params=parse_key(params, "fast"),
            name='fast_T1')

        fast_T1.inputs.output_biascorrected = True
        fast_T1.inputs.output_biasfield = True

        seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                         fast_T1, "in_files")

        seg_pipe.connect(
            inputnode, ('indiv_params', parse_key, "fast"),
            fast_T1, "indiv_params")

        # output node

        # outputnode
        if pad and space == "native":
            pad_debiased_T1 = pad_back(
                seg_pipe, data_preparation_pipe, inputnode,
                fast_T1, "restored_image",
                outputnode, "debiased_T1", params)

    # #### stereo to native
    if "native_to_stereo_pipe" in params.keys():
        if "skull_stripped_template" not in params["native_to_stereo_pipe"]:

            native_to_stereo_pipe = create_native_to_stereo_pipe(
                "native_to_stereo_pipe",
                params=parse_key(params, "native_to_stereo_pipe"))

            seg_pipe.connect(native_to_stereo_pipe,
                             'outputnode.native_to_stereo_trans',
                             outputnode, 'native_to_stereo_trans')

            # full head version
            seg_pipe.connect(data_preparation_pipe, "outputnode.native_T1",
                             native_to_stereo_pipe, 'inputnode.native_T1')

            native_to_stereo_pipe.inputs.inputnode.stereo_T1 = \
                params_template_stereo["template_head"]

            seg_pipe.connect(native_to_stereo_pipe,
                             "outputnode.stereo_native_T1",
                             outputnode, "stereo_native_T1")

            if pad:
                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    pad_debiased_T1, "out_file",
                    outputnode, "stereo_debiased_T1")

    #  extract brain pipeline
    if "extract_pipe" not in params.keys():
        print("Error, extract_pipe was not found in params, \
            skipping")
        return seg_pipe

    extract_T1_pipe = create_extract_pipe(
        params_template=params_template,
        params=parse_key(params, "extract_pipe"))

    seg_pipe.connect(
        inputnode, "indiv_params",
        extract_T1_pipe, "inputnode.indiv_params")

    if "N4debias" in params.keys():

        # brain extraction
        seg_pipe.connect(N4debias_T1, "output_image",
                         extract_T1_pipe, "inputnode.restore_T1")

    elif "fast" in params.keys():

        # brain extraction
        seg_pipe.connect(
            fast_T1, ("restored_image", show_files),
            extract_T1_pipe, "inputnode.restore_T1")

    else:

        # brain extraction (with atlasbrex)
        seg_pipe.connect(
            inputnode, "preproc_T1",
            extract_T1_pipe, "inputnode.restore_T1")

    if pad and space == "native":
        pad_mask = pad_back(
            seg_pipe, data_preparation_pipe, inputnode,
            extract_T1_pipe, "smooth_mask.out_file",
            outputnode, "brain_mask", params)

    else:
        seg_pipe.connect(extract_T1_pipe, "smooth_mask.out_file",
                         outputnode, "brain_mask")

    # mask T1 using brain mask and perform N4 bias correction

    # restore_mask_T1
    restore_mask_T1 = pe.Node(fsl.ApplyMask(), name='restore_mask_T1')

    if "N4debias" in params.keys():

        # brain extraction
        seg_pipe.connect(N4debias_T1, "output_image",
                         restore_mask_T1, 'in_file')

    elif "fast" in params.keys():

        # brain extraction
        seg_pipe.connect(
            fast_T1, ("restored_image", show_files),
            restore_mask_T1, 'in_file')

    else:
        seg_pipe.connect(
            inputnode, "preproc_T1",
            restore_mask_T1, 'in_file')

    seg_pipe.connect(extract_T1_pipe, "smooth_mask.out_file",
                     restore_mask_T1, 'mask_file')

    # output masked brain T1
    if pad and space == "native":
        pad_masked_debiased_T1 = pad_back(
            seg_pipe, data_preparation_pipe, inputnode,
            restore_mask_T1, 'out_file',
            outputnode, "masked_debiased_T1", params)

    else:
        seg_pipe.connect(restore_mask_T1, 'out_file',
                         outputnode, 'masked_debiased_T1')

    # #### stereo to native
    if "native_to_stereo_pipe" in params.keys():

        if "skull_stripped_template" in params["native_to_stereo_pipe"]:

            native_to_stereo_pipe = create_native_to_stereo_pipe(
                "native_to_stereo_pipe",
                params=parse_key(params, "native_to_stereo_pipe"))

            seg_pipe.connect(native_to_stereo_pipe,
                             'outputnode.native_to_stereo_trans',
                             outputnode, 'native_to_stereo_trans')

            print("Found skull_stripped_template in native_to_stereo_pipe")

            if pad:

                # skull stripped version
                print("using skull_stripped_template for stereotaxic norm")

                seg_pipe.connect(
                    pad_masked_debiased_T1, "out_file",
                    native_to_stereo_pipe,
                    'inputnode.native_T1')

                seg_pipe.connect(native_to_stereo_pipe,
                                 'outputnode.stereo_native_T1',
                                 outputnode, "stereo_masked_debiased_T1")

                native_to_stereo_pipe.inputs.inputnode.stereo_T1 = \
                    params_template_stereo["template_brain"]

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    data_preparation_pipe, "outputnode.native_T1",
                    outputnode, "stereo_native_T1")

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    pad_debiased_T1, "out_file",
                    outputnode, "stereo_debiased_T1")

            else:
                # full head version
                seg_pipe.connect(data_preparation_pipe, "outputnode.native_T1",
                                 native_to_stereo_pipe, 'inputnode.native_T1')

                native_to_stereo_pipe.inputs.inputnode.stereo_T1 = \
                    params_template_stereo["template_head"]

                seg_pipe.connect(native_to_stereo_pipe,
                                 "outputnode.stereo_native_T1",
                                 outputnode, "stereo_native_T1")

        else:

            if pad:

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    pad_masked_debiased_T1, "out_file",
                    outputnode, "stereo_masked_debiased_T1")

        # now for every pipeline (skull_stripped_template or not)
        if pad:
            if "extract_pipe" in params.keys():

                apply_to_stereo(
                    seg_pipe, native_to_stereo_pipe,
                    pad_mask, "out_file",
                    outputnode, "stereo_brain_mask")

    # full_segment (restarting from the avg_align files)
    if "brain_segment_pipe" not in params.keys():
        print("Error, brain_segment_pipe was not found in params, \
            skipping")
        return seg_pipe

    brain_segment_pipe = create_brain_segment_from_mask_pipe(
        params_template=params_template,
        params=parse_key(params, "brain_segment_pipe"), space=space)

    seg_pipe.connect(restore_mask_T1, 'out_file',
                     brain_segment_pipe, 'inputnode.masked_debiased_T1')

    seg_pipe.connect(inputnode, 'indiv_params',
                     brain_segment_pipe, 'inputnode.indiv_params')

    if pad and space == "native":

        pad_seg_mask = pad_back(
            seg_pipe, data_preparation_pipe, inputnode,
            brain_segment_pipe, "outputnode.segmented_file",
            outputnode, "segmented_brain_mask", params)

        pad_prob_gm = pad_back(
            seg_pipe, data_preparation_pipe, inputnode,
            brain_segment_pipe, "outputnode.prob_gm",
            outputnode, "prob_gm", params)

        pad_prob_wm = pad_back(
            seg_pipe, data_preparation_pipe, inputnode,
            brain_segment_pipe, "outputnode.prob_wm",
            outputnode, "prob_wm", params)

        pad_prob_csf = pad_back(
            seg_pipe, data_preparation_pipe, inputnode,
            brain_segment_pipe, "outputnode.prob_csf",
            outputnode, "prob_csf", params)

    else:
        seg_pipe.connect(brain_segment_pipe, 'outputnode.segmented_file',
                         outputnode, 'segmented_brain_mask')

        seg_pipe.connect(brain_segment_pipe, 'outputnode.prob_csf',
                         outputnode, 'prob_csf')

        seg_pipe.connect(brain_segment_pipe, 'outputnode.prob_gm',
                         outputnode, 'prob_gm')

        seg_pipe.connect(brain_segment_pipe, 'outputnode.prob_wm',
                         outputnode, 'prob_wm')

    if "export_5tt_pipe" in params["brain_segment_pipe"]:
        if pad and space == "native":
            pad_back(
                seg_pipe, data_preparation_pipe, inputnode,
                brain_segment_pipe, "outputnode.gen_5tt",
                outputnode, "gen_5tt", params)

    if "native_to_stereo_pipe" in params.keys() and pad:

        apply_to_stereo(
            seg_pipe, native_to_stereo_pipe,
            pad_prob_gm, "out_file",
            outputnode, "stereo_prob_gm")

        apply_to_stereo(
            seg_pipe, native_to_stereo_pipe,
            pad_prob_wm, "out_file",
            outputnode, "stereo_prob_wm")

        apply_to_stereo(
            seg_pipe, native_to_stereo_pipe,
            pad_prob_csf, "out_file",
            outputnode, "stereo_prob_csf")

        apply_stereo_seg_mask = apply_to_stereo(
            seg_pipe, native_to_stereo_pipe,
            pad_seg_mask, "out_file",
            outputnode, "stereo_segmented_brain_mask")

    if "nii2mesh_brain_pipe" in params["brain_segment_pipe"]:

        nii2mesh_brain_pipe = create_nii2mesh_brain_pipe(
            params=parse_key(params["brain_segment_pipe"],
                             "nii2mesh_brain_pipe"))

        if pad:
            if "native_to_stereo_pipe" in params.keys():

                seg_pipe.connect(apply_stereo_seg_mask, "out_file",
                                 nii2mesh_brain_pipe,
                                 'inputnode.segmented_file')

                seg_pipe.connect(nii2mesh_brain_pipe, "outputnode.wmgm_stl",
                                 outputnode, 'stereo_wmgm_stl')

                seg_pipe.connect(nii2mesh_brain_pipe, "outputnode.wmgm_nii",
                                 outputnode, 'stereo_wmgm_mask')

            elif space == "native":
                seg_pipe.connect(pad_seg_mask, "out_file",
                                 nii2mesh_brain_pipe,
                                 'inputnode.segmented_file')
        else:
            seg_pipe.connect(brain_segment_pipe, "outputnode.segmented_file",
                             nii2mesh_brain_pipe, 'inputnode.segmented_file')

        seg_pipe.connect(nii2mesh_brain_pipe, "outputnode.wmgm_stl",
                         outputnode, 'wmgm_stl')

        seg_pipe.connect(nii2mesh_brain_pipe, "outputnode.wmgm_nii",
                         outputnode, 'wmgm_mask')

    elif "IsoSurface_brain_pipe" in params["brain_segment_pipe"]:

        IsoSurface_brain_pipe = create_IsoSurface_brain_pipe(
            params=parse_key(params["brain_segment_pipe"],
                             "IsoSurface_brain_pipe"))

        if pad:
            if "native_to_stereo_pipe" in params.keys():

                seg_pipe.connect(apply_stereo_seg_mask, "out_file",
                                 IsoSurface_brain_pipe,
                                 'inputnode.segmented_file')

                seg_pipe.connect(IsoSurface_brain_pipe, "outputnode.wmgm_stl",
                                 outputnode, 'stereo_wmgm_stl')

                seg_pipe.connect(IsoSurface_brain_pipe, "outputnode.wmgm_nii",
                                 outputnode, 'stereo_wmgm_mask')

            elif space == "native":
                seg_pipe.connect(pad_seg_mask, "out_file",
                                 IsoSurface_brain_pipe,
                                 'inputnode.segmented_file')
        else:
            seg_pipe.connect(brain_segment_pipe, "outputnode.segmented_file",
                             IsoSurface_brain_pipe, 'inputnode.segmented_file')

        seg_pipe.connect(IsoSurface_brain_pipe, "outputnode.wmgm_stl",
                         outputnode, 'wmgm_stl')

        seg_pipe.connect(IsoSurface_brain_pipe, "outputnode.wmgm_nii",
                         outputnode, 'wmgm_mask')

    return seg_pipe
