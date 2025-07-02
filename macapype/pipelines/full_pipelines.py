"""
    Gather all full pipelines

"""
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from nipype.interfaces import fsl

from nipype.interfaces.ants.utils import ImageMath

from nipype.interfaces.niftyreg.regutils import RegResample

from ..utils.utils_nodes import NodeParams

from macapype.nodes.correct_bias import T1xT2BiasFieldCorrection
from macapype.nodes.register import IterREGBET

from macapype.nodes.pad import pad_back

from .prepare import (create_short_preparation_pipe,
                      create_short_preparation_T1_pipe)

from .segment import (create_old_segment_pipe,
                      create_native_old_segment_pipe,
                      create_segment_atropos_pipe,
                      create_segment_atropos_seg_pipe,
                      create_mask_from_seg_pipe,
                      create_5tt_pipe)

from .correct_bias import create_masked_correct_bias_pipe

from .register import (create_register_NMT_pipe, create_reg_seg_pipe)

from .extract_brain import create_extract_pipe

from .surface import (create_nii2mesh_brain_pipe, create_IsoSurface_brain_pipe,
                      create_IsoSurface_tissues_pipe)

from macapype.utils.misc import parse_key, list_input_files

###############################################################################
# SPM based segmentation (from: Régis Trapeau)
# -soft SPM or SPM_T1
###############################################################################


def create_brain_old_segment_from_mask_pipe(
        params_template, params={},
        name="brain_old_segment_from_mask_pipe", space="native"):

    brain_old_segment_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['masked_debiased_T1', "debiased_T1", 'indiv_params']),
        name='inputnode')

    # creating outputnode
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["segmented_file",
                    "threshold_gm", "threshold_wm", "threshold_csf",
                    "prob_gm", "prob_wm", "prob_csf"]),
        name='outputnode')

    # Iterative registration to the INIA19 template
    if "reg" not in params.keys():

        print("No reg, skipping")
        return brain_old_segment_pipe

    reg = NodeParams(IterREGBET(),
                     params=parse_key(params, "reg"),
                     name='reg')

    reg.inputs.refb_file = params_template_brainmask["template_brain"]

    brain_old_segment_pipe.connect(inputnode, 'debiased_T1',
                     reg, 'inw_file')

    brain_old_segment_pipe.connect(inputnode, 'masked_debiased_T1',
                     reg, 'inb_file')

    brain_old_segment_pipe.connect(inputnode, ('indiv_params', parse_key, "reg"),
                     reg, 'indiv_params')

    # Compute brain mask using old_segment of SPM and postprocessing on
    # tissues' masks
    if "old_segment_pipe" not in params.keys():
        print("No segmentation, skipping")
        return brain_old_segment_pipe

    if space == "template":

        old_segment_pipe = create_old_segment_pipe(
            params_template_seg, params=parse_key(params, "old_segment_pipe"))

        brain_old_segment_pipe.connect(reg, 'warp_file',
                         old_segment_pipe, 'inputnode.T1')

        brain_old_segment_pipe.connect(inputnode, 'indiv_params',
                         old_segment_pipe, 'inputnode.indiv_params')

    elif space == "native":

        old_segment_pipe = create_native_old_segment_pipe(
            params_template_seg, params=parse_key(params, "old_segment_pipe"))

        brain_old_segment_pipe.connect(reg, 'inv_transfo_file',
                         old_segment_pipe, 'inputnode.inv_transfo_file')

        brain_old_segment_pipe.connect(debias, 't1_debiased_brain_file',
                         old_segment_pipe, 'inputnode.native_T1')

        brain_old_segment_pipe.connect(inputnode, 'indiv_params',
                         old_segment_pipe, 'inputnode.indiv_params')
    else:

        print("Error, space={}".format(space))
        return brain_old_segment_pipe

    # outputnode
    brain_old_segment_pipe.connect(
        old_segment_pipe, 'outputnode.prob_wm',
        outputnode, 'prob_wm')

    brain_old_segment_pipe.connect(
        old_segment_pipe, 'outputnode.prob_csf',
        outputnode, 'prob_csf')

    brain_old_segment_pipe.connect(
        old_segment_pipe, 'outputnode.prob_gm',
        outputnode, 'prob_gm')

    brain_old_segment_pipe.connect(
        old_segment_pipe, 'outputnode.threshold_wm',
        outputnode, 'threshold_wm')

    brain_old_segment_pipe.connect(
        old_segment_pipe, 'outputnode.threshold_csf',
        outputnode, 'threshold_csf')

    brain_old_segment_pipe.connect(
        old_segment_pipe, 'outputnode.threshold_gm',
        outputnode, 'threshold_gm')

    # mask_from_seg_pipe
    if not mask_from_seg_pipe in params:
        print("** Warning, segmented file will not be provided, \
            missing mask_from_seg_pipe in brain_old_segment_pipe**")

    mask_from_seg_pipe = create_mask_from_seg_pipe(
        params=parse_key(params, "mask_from_seg_pipe"))

    brain_old_segment_pipe.connect(old_segment_pipe, 'outputnode.threshold_csf',
                        mask_from_seg_pipe, 'inputnode.mask_csf')

    brain_old_segment_pipe.connect(old_segment_pipe, 'outputnode.threshold_wm',
                        mask_from_seg_pipe, 'inputnode.mask_wm')

    brain_old_segment_pipe.connect(old_segment_pipe, 'outputnode.threshold_gm',
                        mask_from_seg_pipe, 'inputnode.mask_gm')

    brain_old_segment_pipe.connect(inputnode, 'indiv_params',
                        mask_from_seg_pipe, 'inputnode.indiv_params')

    # outputnode
    brain_old_segment_pipe.connect(mask_from_seg_pipe,
                     'merge_indexed_mask.indexed_mask',
                     outputnode, 'segmented_file')

    return brain_old_segment_pipe

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
            fields=["segmented_file",
                    "threshold_gm", "threshold_wm", "threshold_csf",
                    "prob_gm", "prob_wm", "prob_csf"]),
        name='outputnode')

    if "use_priors" in params["segment_atropos_pipe"].keys():

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
            # Iterative registration to the template
            reg = NodeParams(
                IterREGBET(),
                params=parse_key(params, "reg"),
                name='reg')

            reg.inputs.refb_file = params_template["template_brain"]

            if "nonlin_reg" in params["reg"]:
                reg.inputs.refw_file = params_template["template_head"]
                reg.inputs.k = True

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
                register_gm_to_nat.inputs.output_type = "NIFTI_GZ"  # for SPM
                register_gm_to_nat.inputs.interp = "nearestneighbour"

                register_gm_to_nat.inputs.in_file = \
                    params_template["template_gm"]

                brain_segment_pipe.connect(
                    inputnode, 'masked_debiased_T1',
                    register_gm_to_nat, 'reference')

                brain_segment_pipe.connect(
                    reg, 'inv_transfo_file',
                    register_gm_to_nat, "in_matrix_file")

                # wm
                register_wm_to_nat = pe.Node(
                    fsl.ApplyXFM(), name="register_wm_to_nat")
                register_wm_to_nat.inputs.output_type = "NIFTI_GZ"  # for SPM
                register_wm_to_nat.inputs.interp = "nearestneighbour"

                register_wm_to_nat.inputs.in_file = \
                    params_template["template_wm"]

                brain_segment_pipe.connect(
                    inputnode, 'masked_debiased_T1',
                    register_wm_to_nat, 'reference')

                brain_segment_pipe.connect(
                    reg, 'inv_transfo_file',
                    register_wm_to_nat, "in_matrix_file")

                # csf
                register_csf_to_nat = pe.Node(
                    fsl.ApplyXFM(), name="register_csf_to_nat")
                register_csf_to_nat.inputs.output_type = "NIFTI_GZ"  # for SPM
                register_csf_to_nat.inputs.interp = "nearestneighbour"

                register_csf_to_nat.inputs.in_file = \
                    params_template["template_csf"]

                brain_segment_pipe.connect(
                    inputnode, 'masked_debiased_T1',
                    register_csf_to_nat, 'reference')

                brain_segment_pipe.connect(
                    reg, 'inv_transfo_file',
                    register_csf_to_nat, "in_matrix_file")
        else:
            print("##### Error, no coregistration method is defined")
            return brain_segment_pipe

    # ants Atropos
    if "template_seg" in params_template.keys():

        print("#### create_segment_atropos_seg_pipe ")
        segment_atropos_pipe = create_segment_atropos_seg_pipe(
            params=parse_key(params, "segment_atropos_pipe"))

        # linking priors if "use_priors" in params
        if "use_priors" in params["segment_atropos_pipe"].keys():

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
                    register_wm_to_nat, "out_file",
                    segment_atropos_pipe, "inputnode.wm_prior_file")

    # input to segment_atropos_pipe
    brain_segment_pipe.connect(
        inputnode, 'masked_debiased_T1',
        segment_atropos_pipe, "inputnode.brain_file")

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
        # outputnodes
        brain_segment_pipe.connect(reg_seg_pipe, 'outputnode.norm_prob_gm',
                                   outputnode, 'prob_gm')
        brain_segment_pipe.connect(reg_seg_pipe, 'outputnode.norm_prob_wm',
                                   outputnode, 'prob_wm')
        brain_segment_pipe.connect(reg_seg_pipe, 'outputnode.norm_prob_csf',
                                   outputnode, 'prob_csf')

    return brain_segment_pipe
 # #############################################################################################################


def create_full_T1T2_subpipes(
        params_template_stereo, params_template_brainmask, params_template_seg,
        params={}, name="full_T1T2_subpipes", mask_file=None,
        space="native", pad=False):
    """Description: Segment T1 (using T2 for bias correction) .

    Params:

    - short_preparation_pipe (see :class:`create_short_preparation_pipe \
    <macapype.pipelines.prepare.create_short_preparation_pipe>`)

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
            fields=[
                    "native_T1", "native_T2",
                    'stereo_T1', 'stereo_T2',
                    "stereo_padded_T1",
                    "stereo_padded_T2",

                    "stereo_denoised_T1",
                    "native_denoised_T1",

                    "stereo_denoised_T2",
                    "native_denoised_T2",

                    'stereo_debiased_T1', 'stereo_debiased_T2',
                    "native_debiased_T1", "native_debiased_T2",

                    'stereo_brain_mask',
                    'stereo_padded_brain_mask',
                    'stereo_masked_debiased_T1',
                    'stereo_masked_debiased_T2',

                    'native_brain_mask',
                    "native_masked_debiased_T1",
                    "native_masked_debiased_T2",

                    'stereo_segmented_brain_mask',
                    'stereo_padded_segmented_brain_mask',
                    'stereo_prob_gm', 'stereo_prob_wm', 'stereo_prob_csf',
                    "stereo_gen_5tt",

                    'native_segmented_brain_mask',
                    'native_prob_gm', 'native_prob_wm', 'native_prob_csf',
                    "native_gen_5tt",

                    "stereo_wmgm_mask",
                    "native_wmgm_mask",
                    "wmgm_stl",

                    "csf_stl",
                    "gm_stl",
                    "wm_stl",

                    "stereo_to_native_trans",
                    "native_to_stereo_trans"]),
        name='outputnode')

    # ##################################### preprocessing
    if 'short_preparation_pipe' in params.keys():
        data_preparation_pipe = create_short_preparation_pipe(
            params=parse_key(params, "short_preparation_pipe"),
            params_template=params_template_stereo)

    else:
        print("Error, short_preparation_pipe \
            was not found in params, skipping")

        test_node = pe.Node(niu.Function(input_names=['list_T1', 'list_T2'],
                                         output_names=[''],
                                         function=list_input_files),
                            name="test_node")

        seg_pipe.connect(inputnode, 'list_T1',
                         test_node, 'list_T1')
        seg_pipe.connect(inputnode, 'list_T2',
                         test_node, 'list_T2')

        return seg_pipe

    # inputs
    seg_pipe.connect(inputnode, 'list_T1',
                     data_preparation_pipe, 'inputnode.list_T1')

    seg_pipe.connect(inputnode, 'list_T2',
                     data_preparation_pipe, 'inputnode.list_T2')

    seg_pipe.connect(inputnode, 'indiv_params',
                     data_preparation_pipe, 'inputnode.indiv_params')

    # outputnode
    seg_pipe.connect(data_preparation_pipe, 'outputnode.native_T1',
                     outputnode, 'native_T1')

    seg_pipe.connect(data_preparation_pipe, 'outputnode.native_T2',
                     outputnode, 'native_T2')

    # everything is now in stereo space
    if "denoise" in params["short_preparation_pipe"].keys():
        seg_pipe.connect(data_preparation_pipe,
                         'outputnode.stereo_denoised_T1',
                         outputnode, 'stereo_denoised_T1')

        seg_pipe.connect(data_preparation_pipe,
                         'outputnode.stereo_denoised_T2',
                         outputnode, 'stereo_denoised_T2')

        if pad and space == "native":
            pad_back(
                seg_pipe, data_preparation_pipe,
                data_preparation_pipe, "outputnode.stereo_denoised_T1",
                outputnode, "native_denoised_T1", params,
                inter_val="LIN")

            pad_back(
                seg_pipe, data_preparation_pipe,
                data_preparation_pipe, "outputnode.stereo_denoised_T2",
                outputnode, "native_denoised_T2", params,
                inter_val="LIN")

    seg_pipe.connect(data_preparation_pipe, 'outputnode.stereo_T1',
                     outputnode, "stereo_T1")

    seg_pipe.connect(data_preparation_pipe, 'outputnode.stereo_T2',
                     outputnode, "stereo_T2")

    seg_pipe.connect(data_preparation_pipe, "outputnode.stereo_padded_T1",
                     outputnode, "stereo_padded_T1")

    seg_pipe.connect(data_preparation_pipe, "outputnode.stereo_padded_T2",
                     outputnode, "stereo_padded_T2")

    if ("fast" in params["short_preparation_pipe"]
            or "N4debias" in params["short_preparation_pipe"]
            or "itk_debias" in params["short_preparation_pipe"]):

        # debiased
        seg_pipe.connect(
            data_preparation_pipe, 'outputnode.stereo_debiased_T1',
            outputnode, 'stereo_debiased_T1')

        seg_pipe.connect(
            data_preparation_pipe, 'outputnode.stereo_debiased_T2',
            outputnode, 'stereo_debiased_T2')

        if pad:

            pad_back(
                seg_pipe, data_preparation_pipe,
                data_preparation_pipe, "outputnode.stereo_debiased_T1",
                outputnode, "native_debiased_T1", params, inter_val="LIN")

            pad_back(
                seg_pipe, data_preparation_pipe,
                data_preparation_pipe, "outputnode.stereo_debiased_T2",
                outputnode, "native_debiased_T2", params, inter_val="LIN")

    seg_pipe.connect(
        data_preparation_pipe, "outputnode.stereo_to_native_trans",
        outputnode, 'stereo_to_native_trans')

    seg_pipe.connect(
        data_preparation_pipe, "outputnode.native_to_stereo_trans",
        outputnode, 'native_to_stereo_trans')

    # ############################################ extract mask
    print("mask file {}".format(mask_file))

    if mask_file is None:

        # full extract brain pipeline (correct_bias, denoising, extract brain)
        if "extract_pipe" in params.keys():

            print("Found extract_pipe")

            # brain extraction
            extract_pipe = create_extract_pipe(
                params_template=params_template_brainmask,
                params=parse_key(params, "extract_pipe"))

            seg_pipe.connect(inputnode, "indiv_params",
                                        extract_pipe, "inputnode.indiv_params")

            if "use_T2" in params["extract_pipe"]:

                seg_pipe.connect(
                        data_preparation_pipe, "outputnode.stereo_debiased_T2",
                        extract_pipe, "inputnode.restore_T1")

            else:

                seg_pipe.connect(
                        data_preparation_pipe, "outputnode.stereo_debiased_T1",
                        extract_pipe, "inputnode.restore_T1")

            # outputnode
            seg_pipe.connect(
                extract_pipe, "outputnode.mask_file",
                outputnode, "stereo_brain_mask")

            if "pad_template" in params["short_preparation_pipe"].keys():

                pad_stereo_brain_mask = NodeParams(
                    ImageMath(),
                    params=parse_key(params["short_preparation_pipe"],
                                     "pad_template"),
                    name="pad_stereo_brain_mask")

                seg_pipe.connect(
                    extract_pipe, "outputnode.mask_file",
                    pad_stereo_brain_mask, "op1")

                seg_pipe.connect(
                    pad_stereo_brain_mask, "output_image",
                    outputnode, "stereo_padded_brain_mask")

            if pad:
                pad_back(
                    seg_pipe, data_preparation_pipe,
                    extract_pipe, "outputnode.mask_file",
                    outputnode, "native_brain_mask", params)

        # full extract brain pipeline (correct_bias, denoising, extract brain)
        elif "debias" in params.keys():

            print("Found debias without extract_pipe")

            # Bias correction of cropped images
            debias = NodeParams(T1xT2BiasFieldCorrection(),
                                params=parse_key(params, "debias"),
                                name='debias')

            seg_pipe.connect(
                data_preparation_pipe, "outputnode.stereo_debiased_T1",
                debias, 't1_file')

            seg_pipe.connect(
                data_preparation_pipe, "outputnode.stereo_debiased_T2",
                debias, 't2_file')

            debias.inputs.bet = 1

            # outputnode
            seg_pipe.connect(
                debias, "debiased_mask_file",
                outputnode, "stereo_brain_mask")

            if pad:
                pad_back(
                    seg_pipe, data_preparation_pipe,
                    debias, "debiased_mask_file",
                    outputnode, "native_brain_mask", params)

            # TODO is not used now...
            seg_pipe.connect(
                inputnode, ('indiv_params', parse_key, "debias"),
                debias, 'indiv_params')

            # outputnode
            seg_pipe.connect(
                debias, 't1_debiased_brain_file',
                outputnode, "stereo_masked_debiased_T1")

            seg_pipe.connect(
                debias, 't2_debiased_brain_file',
                outputnode, "stereo_masked_debiased_T2")

            if pad:
                pad_back(
                    seg_pipe, data_preparation_pipe,
                    debias, 't1_debiased_brain_file',
                    outputnode, "native_masked_debiased_T1", params,
                    inter_val="LIN")

                pad_back(
                    seg_pipe, data_preparation_pipe,
                    debias, 't2_debiased_brain_file',
                    outputnode, "native_masked_debiased_T2", params,
                    inter_val="LIN")

        else:
            print("no extract_brain method is defined, skipping")
            return seg_pipe

    else:
        print("Using native external mask {}".format(mask_file))
        outputnode.inputs.native_brain_mask = mask_file

        # apply transfo to list
        apply_crop_external_mask = pe.Node(RegResample(inter_val="NN"),
                                           name='apply_crop_external_mask')

        apply_crop_external_mask.inputs.flo_file = mask_file

        seg_pipe.connect(data_preparation_pipe,
                         'outputnode.native_to_stereo_trans',
                         apply_crop_external_mask, "trans_file")

        seg_pipe.connect(data_preparation_pipe, "outputnode.stereo_T1",
                         apply_crop_external_mask, "ref_file")

        # outputnode
        seg_pipe.connect(apply_crop_external_mask, "out_file",
                         outputnode, "stereo_brain_mask")

    # ################################################ masked_debias ##

    # correcting for bias T1/T2, but this time with a mask
    if "masked_correct_bias_pipe" in params.keys():

        masked_correct_bias_pipe = create_masked_correct_bias_pipe(
            params=parse_key(params, "masked_correct_bias_pipe"))

        seg_pipe.connect(
            data_preparation_pipe, "outputnode.stereo_debiased_T1",
            masked_correct_bias_pipe, "inputnode.preproc_T1")

        seg_pipe.connect(
            data_preparation_pipe, "outputnode.stereo_debiased_T2",
            masked_correct_bias_pipe, "inputnode.preproc_T2")

        if mask_file is None:
            seg_pipe.connect(extract_pipe, "outputnode.mask_file",
                             masked_correct_bias_pipe, "inputnode.brain_mask")

        else:
            seg_pipe.connect(apply_crop_external_mask, "out_file",
                             masked_correct_bias_pipe, "inputnode.brain_mask")

        # outputnode
        seg_pipe.connect(
            masked_correct_bias_pipe,
            'outputnode.mask_debiased_T1',
            outputnode, "stereo_masked_debiased_T1")

        seg_pipe.connect(
            masked_correct_bias_pipe,
            'outputnode.mask_debiased_T2',
            outputnode, "stereo_masked_debiased_T1")

        if pad:

            pad_back(
                seg_pipe, data_preparation_pipe,
                masked_correct_bias_pipe,
                'outputnode.mask_debiased_T1',
                outputnode, "native_masked_debiased_T1", params,
                inter_val="LIN")

            pad_back(
                seg_pipe, data_preparation_pipe,
                masked_correct_bias_pipe,
                'outputnode.mask_debiased_T2',
                outputnode, "native_masked_debiased_T2", params,
                inter_val="LIN")

    elif "debias" in params.keys():
        if "extract_pipe" in params.keys():

            print("Found debias AND extract_pipe")

            # Bias correction of cropped images
            debias = NodeParams(T1xT2BiasFieldCorrection(),
                                params=parse_key(params, "debias"),
                                name='debias')

            seg_pipe.connect(
                data_preparation_pipe, "outputnode.stereo_debiased_T1",
                debias, 't1_file')

            seg_pipe.connect(
                data_preparation_pipe, "outputnode.stereo_debiased_T2",
                debias, 't2_file')

            if mask_file is None:
                if "extract_pipe" in params.keys():
                    seg_pipe.connect(
                        extract_pipe, "outputnode.mask_file",
                        debias, 'b')
                else:
                    debias.inputs.bet = 1

                    # outputnode
                    seg_pipe.connect(
                        debias, "debiased_mask_file",
                        outputnode, "stereo_brain_mask")

                    if pad:
                        pad_back(
                            seg_pipe, data_preparation_pipe,
                            debias, "debiased_mask_file",
                            outputnode, "native_brain_mask", params)

            else:
                seg_pipe.connect(
                    apply_crop_external_mask, "out_file",
                    debias, 'b')

            # TODO is not used now...
            seg_pipe.connect(
                inputnode, ('indiv_params', parse_key, "debias"),
                debias, 'indiv_params')

            # outputnode
            seg_pipe.connect(
                debias, 't1_debiased_brain_file',
                outputnode, "stereo_masked_debiased_T1")

            seg_pipe.connect(
                debias, 't2_debiased_brain_file',
                outputnode, "stereo_masked_debiased_T2")

            if pad:
                pad_back(
                    seg_pipe, data_preparation_pipe,
                    debias, 't1_debiased_brain_file',
                    outputnode, "native_masked_debiased_T1", params,
                    inter_val="LIN")

                pad_back(
                    seg_pipe, data_preparation_pipe,
                    debias, 't2_debiased_brain_file',
                    outputnode, "native_masked_debiased_T2", params,
                    inter_val="LIN")
        else:
            print('debias performed brain extraction as well')

    else:

        print("No T1*T2 debias will be performed")

        # restore_mask_T1
        restore_mask_T1 = pe.Node(fsl.ApplyMask(), name='restore_mask_T1')

        # restore_mask_T2
        restore_mask_T2 = pe.Node(fsl.ApplyMask(), name='restore_mask_T2')

        seg_pipe.connect(
            data_preparation_pipe, "outputnode.stereo_debiased_T1",
            restore_mask_T1, 'in_file')

        seg_pipe.connect(
            data_preparation_pipe, "outputnode.stereo_debiased_T2",
            restore_mask_T2, 'in_file')

        if mask_file is None:
            if "extract_pipe" in params.keys():
                seg_pipe.connect(
                    extract_pipe, "outputnode.mask_file",
                    restore_mask_T1, 'mask_file')

                seg_pipe.connect(
                    extract_pipe, "outputnode.mask_file",
                    restore_mask_T2, 'mask_file')
            else:
                print("!!!!! Error, no brain mask is available, skipping")
                return seg_pipe
        else:
            seg_pipe.connect(
                apply_crop_external_mask, "out_file",
                restore_mask_T1, 'mask_file')

            seg_pipe.connect(
                apply_crop_external_mask, "out_file",
                restore_mask_T2, 'mask_file')

        # outputnode
        seg_pipe.connect(
            restore_mask_T1, 'out_file',
            outputnode, "stereo_masked_debiased_T1")

        seg_pipe.connect(
            restore_mask_T2, 'out_file',
            outputnode, "stereo_masked_debiased_T2")

        if pad:
            pad_back(
                seg_pipe, data_preparation_pipe,
                restore_mask_T1, 'out_file',
                outputnode, "native_masked_debiased_T1", params,
                inter_val="LIN")

            pad_back(
                seg_pipe, data_preparation_pipe,
                restore_mask_T2, 'out_file',
                outputnode, "native_masked_debiased_T2", params,
                inter_val="LIN")

    # ################################### brain_segment
    # (restarting from the avg_align files)
    if "brain_segment_pipe" in params.keys():
        brain_segment_pipe = create_brain_segment_from_mask_pipe(
            params_template=params_template_seg,
            params=parse_key(params, "brain_segment_pipe"), space=space)

    elif brain_old_segment_pipe in params.keys():
        brain_segment_pipe = create_brain_old_segment_from_mask_pipe(
            params_template=params_template_seg,
            params=parse_key(params, "brain_old_segment_pipe"), space=space)

    else:
        return seg_pipe

    seg_pipe.connect(inputnode, 'indiv_params',
                     brain_segment_pipe, 'inputnode.indiv_params')

    if 'use_T2' in params['brain_segment_pipe'].keys():

        # using T2
        if "masked_correct_bias_pipe" in params.keys():
            seg_pipe.connect(
                masked_correct_bias_pipe, 'outputnode.mask_debiased_T2',
                brain_segment_pipe, 'inputnode.masked_debiased_T1')

            seg_pipe.connect(
                data_preparation_pipe, "outputnode.stereo_debiased_T2",
                brain_segment_pipe, 'inputnode.debiased_T1')

        elif "debias" in params.keys():
            seg_pipe.connect(
                debias, 't2_debiased_brain_file',
                brain_segment_pipe, 'inputnode.masked_debiased_T1')

            seg_pipe.connect(
                debias, 't2_debiased_file',
                brain_segment_pipe, 'inputnode.debiased_T1')

        else:
            seg_pipe.connect(
                restore_mask_T2, 'out_file',
                brain_segment_pipe, 'inputnode.masked_debiased_T1')

            seg_pipe.connect(
                data_preparation_pipe, "outputnode.stereo_debiased_T2",
                brain_segment_pipe, 'inputnode.debiased_T1')

    else:

        # using T1
        if "masked_correct_bias_pipe" in params.keys():
            seg_pipe.connect(
                masked_correct_bias_pipe, 'outputnode.mask_debiased_T1',
                brain_segment_pipe, 'inputnode.masked_debiased_T1')

            seg_pipe.connect(
                data_preparation_pipe, "outputnode.stereo_debiased_T1",
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

            seg_pipe.connect(
                data_preparation_pipe, "outputnode.stereo_debiased_T1",
                brain_segment_pipe, 'inputnode.debiased_T1')

    # outputnode
    seg_pipe.connect(brain_segment_pipe, 'outputnode.segmented_file',
                     outputnode, 'stereo_segmented_brain_mask')

    seg_pipe.connect(brain_segment_pipe, 'outputnode.prob_gm',
                     outputnode, 'stereo_prob_gm')

    seg_pipe.connect(brain_segment_pipe, 'outputnode.prob_wm',
                     outputnode, 'stereo_prob_wm')

    seg_pipe.connect(brain_segment_pipe, 'outputnode.prob_csf',
                     outputnode, 'stereo_prob_csf')

    if pad and space == "native":
        pad_back(
            seg_pipe, data_preparation_pipe,
            brain_segment_pipe, "outputnode.segmented_file",
            outputnode, "native_segmented_brain_mask", params)
        pad_back(
            seg_pipe, data_preparation_pipe,
            brain_segment_pipe, "outputnode.prob_gm",
            outputnode, "native_prob_gm", params,
            inter_val="LIN")
        pad_back(
            seg_pipe, data_preparation_pipe,
            brain_segment_pipe, "outputnode.prob_wm",
            outputnode, "native_prob_wm", params,
            inter_val="LIN")
        pad_back(
            seg_pipe, data_preparation_pipe,
            brain_segment_pipe, "outputnode.prob_csf",
            outputnode, "native_prob_csf", params,
            inter_val="LIN")

    if "pad_template" in params["short_preparation_pipe"].keys():
        pad_stereo_stereo_brain_mask = NodeParams(
            ImageMath(),
            params=parse_key(params["short_preparation_pipe"],
                             "pad_template"),
            name="pad_stereo_stereo_brain_mask")

        seg_pipe.connect(
            brain_segment_pipe, "outputnode.segmented_file",
            pad_stereo_stereo_brain_mask, "op1")

        seg_pipe.connect(
            pad_stereo_stereo_brain_mask, "output_image",
            outputnode, "stereo_padded_segmented_brain_mask")

    # ############################################## export 5tt

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
                                   outputnode, 'stereo_gen_5tt')

        if pad and space == "native":
            pad_back(
                seg_pipe, data_preparation_pipe,
                brain_segment_pipe, "outputnode.gen_5tt",
                outputnode, "native_gen_5tt", params)

    # ############################################## surface

    if "nii2mesh_brain_pipe" in params.keys():

        nii2mesh_brain_pipe = create_nii2mesh_brain_pipe(
            params=parse_key(params["nii2mesh_brain_pipe"]))

        seg_pipe.connect(brain_segment_pipe, "outputnode.segmented_file",
                         nii2mesh_brain_pipe, 'inputnode.segmented_file')

        # outputnode
        seg_pipe.connect(nii2mesh_brain_pipe, "outputnode.wmgm_stl",
                         outputnode, 'wmgm_stl')

        seg_pipe.connect(nii2mesh_brain_pipe, "outputnode.wmgm_nii",
                         outputnode, 'stereo_wmgm_mask')

        if pad:
            pad_back(
                seg_pipe, data_preparation_pipe,
                nii2mesh_brain_pipe, "outputnode.wmgm_nii",
                outputnode, "native_wmgm_mask", params)

    elif "IsoSurface_brain_pipe" in params.keys():

        IsoSurface_brain_pipe = create_IsoSurface_brain_pipe(
            params=parse_key(params["IsoSurface_brain_pipe"]))

        seg_pipe.connect(brain_segment_pipe, "outputnode.segmented_file",
                         IsoSurface_brain_pipe, 'inputnode.segmented_file')

        # outputnode
        seg_pipe.connect(IsoSurface_brain_pipe, "outputnode.wmgm_stl",
                         outputnode, 'wmgm_stl')

        seg_pipe.connect(IsoSurface_brain_pipe, "outputnode.wmgm_nii",
                         outputnode, 'stereo_wmgm_mask')

        if pad:
            pad_back(
                seg_pipe, data_preparation_pipe,
                IsoSurface_brain_pipe, "outputnode.wmgm_nii",
                outputnode, "native_wmgm_mask", params)

    if "IsoSurface_tissues_pipe" in params:

        IsoSurface_tissues_pipe = create_IsoSurface_tissues_pipe(
            params=parse_key(params["IsoSurface_tissues_pipe"]))

        seg_pipe.connect(brain_segment_pipe, "outputnode.threshold_csf",
                         IsoSurface_tissues_pipe, 'inputnode.threshold_csf')

        seg_pipe.connect(brain_segment_pipe, "outputnode.threshold_wm",
                         IsoSurface_tissues_pipe, 'inputnode.threshold_wm')

        seg_pipe.connect(brain_segment_pipe, "outputnode.threshold_gm",
                         IsoSurface_tissues_pipe, 'inputnode.threshold_gm')

        # outputnode
        seg_pipe.connect(IsoSurface_tissues_pipe, "outputnode.csf_stl",
                         outputnode, 'csf_stl')

        seg_pipe.connect(IsoSurface_tissues_pipe, "outputnode.wm_stl",
                         outputnode, 'wm_stl')

        seg_pipe.connect(IsoSurface_tissues_pipe, "outputnode.gm_stl",
                         outputnode, 'gm_stl')

    return seg_pipe


###############################################################################
# ANTS based segmentation for adrien baboons (T1 without T2)
# -soft ANTS_T1


def create_full_T1_subpipes(
        params_template_stereo, params_template_brainmask, params_template_seg,
        params={}, name="full_T1_subpipes", mask_file=None,
        space="native", pad=False):
    """
    Description: Full pipeline to segment T1 (with no T2).

    Params:

    - short_preparation_pipe (see :class:`create_short_preparation_pipe <\
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
            fields=[
                    "native_T1",
                    'stereo_T1',
                    'native_denoised_T1',
                    'stereo_denoised_T1',
                    "stereo_padded_T1",

                    'stereo_brain_mask', 'native_brain_mask',
                    'stereo_debiased_T1', "native_debiased_T1",

                    "native_masked_debiased_T1", "stereo_masked_debiased_T1",

                    'native_segmented_brain_mask', "native_gen_5tt",
                    'native_prob_gm', 'native_prob_wm', 'native_prob_csf',

                    'stereo_segmented_brain_mask', "stereo_gen_5tt",
                    'stereo_prob_gm', 'stereo_prob_wm', 'stereo_prob_csf',

                    "native_wmgm_mask",
                    "stereo_wmgm_mask",
                    "wmgm_stl",

                    "stereo_to_native_trans",
                    "native_to_stereo_trans"]),
        name='outputnode')

    # preprocessing (perform preparation pipe with only T1)
    if 'short_preparation_pipe' in params.keys():
        data_preparation_pipe = create_short_preparation_T1_pipe(
            params=parse_key(params, "short_preparation_pipe"),
            params_template=params_template_stereo)

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

    seg_pipe.connect(data_preparation_pipe, 'outputnode.stereo_T1',
                     outputnode, 'stereo_T1')

    if "denoise" in params["short_preparation_pipe"].keys():
        seg_pipe.connect(
            data_preparation_pipe, 'outputnode.stereo_denoised_T1',
            outputnode, 'stereo_denoised_T1')

        if pad and space == "native":
            pad_back(
                seg_pipe, data_preparation_pipe,
                data_preparation_pipe, "outputnode.stereo_denoised_T1",
                outputnode, "native_denoised_T1", params,
                inter_val="LIN")

    seg_pipe.connect(
        data_preparation_pipe, "outputnode.stereo_padded_T1",
        outputnode, "stereo_padded_T1")

    seg_pipe.connect(
        data_preparation_pipe, "outputnode.native_to_stereo_trans",
        outputnode, 'native_to_stereo_trans')

    seg_pipe.connect(
        data_preparation_pipe, "outputnode.stereo_to_native_trans",
        outputnode, 'stereo_to_native_trans')

    # correct_bias
    seg_pipe.connect(
        data_preparation_pipe, 'outputnode.stereo_debiased_T1',
        outputnode, 'stereo_debiased_T1')

    if pad and space == "native":
        pad_back(
            seg_pipe, data_preparation_pipe,
            data_preparation_pipe, "outputnode.stereo_debiased_T1",
            outputnode, "native_debiased_T1", params,
            inter_val="LIN")

    #  extract brain pipeline
    if "extract_pipe" not in params.keys():
        print("Error, extract_pipe was not found in params, \
            skipping")
        return seg_pipe

    if mask_file is None:

        # brain extraction
        extract_T1_pipe = create_extract_pipe(
            params_template=params_template_brainmask,
            params=parse_key(params, "extract_pipe"))

        seg_pipe.connect(
            inputnode, "indiv_params",
            extract_T1_pipe, "inputnode.indiv_params")

        seg_pipe.connect(
            data_preparation_pipe, 'outputnode.stereo_debiased_T1',
            extract_T1_pipe, "inputnode.restore_T1")

        # outputnode
        seg_pipe.connect(
            extract_T1_pipe, "outputnode.mask_file",
            outputnode, "stereo_brain_mask")

        if pad and space == "native":
            pad_back(
                seg_pipe, data_preparation_pipe,
                extract_T1_pipe, "outputnode.mask_file",
                outputnode, "native_brain_mask", params)

    else:
        print("Using native external mask {}".format(mask_file))
        outputnode.inputs.native_brain_mask = mask_file

        # apply transfo to list
        apply_crop_external_mask = pe.Node(RegResample(inter_val="NN"),
                                           name='apply_crop_external_mask')

        apply_crop_external_mask.inputs.flo_file = mask_file

        seg_pipe.connect(data_preparation_pipe,
                         'outputnode.native_to_stereo_trans',
                         apply_crop_external_mask, "trans_file")

        seg_pipe.connect(data_preparation_pipe, "outputnode.stereo_T1",
                         apply_crop_external_mask, "ref_file")

        # outputnode
        seg_pipe.connect(apply_crop_external_mask, "out_file",
                         outputnode, "stereo_brain_mask")

    # restore_mask_T1
    restore_mask_T1 = pe.Node(fsl.ApplyMask(), name='restore_mask_T1')

    seg_pipe.connect(
            data_preparation_pipe, 'outputnode.stereo_debiased_T1',
            restore_mask_T1, 'in_file')

    if mask_file is None:
        seg_pipe.connect(
            extract_T1_pipe, "outputnode.mask_file",
            restore_mask_T1, 'mask_file')

    else:
        seg_pipe.connect(
            apply_crop_external_mask, "out_file",
            restore_mask_T1, 'mask_file')

    seg_pipe.connect(restore_mask_T1, 'out_file',
                     outputnode, 'stereo_masked_debiased_T1')

    if pad and space == "native":
        pad_back(
            seg_pipe, data_preparation_pipe,
            restore_mask_T1, 'out_file',
            outputnode, "native_masked_debiased_T1", params,
            inter_val="LIN")

    # ### full_segment (restarting from the avg_align files)
    if "brain_segment_pipe" in params.keys():
        brain_segment_pipe = create_brain_segment_from_mask_pipe(
            params_template=params_template_seg,
            params=parse_key(params, "brain_segment_pipe"), space=space)

    elif "brain_old_segment_pipe" in params.keys():
        brain_old_segment_pipe = create_brain_old_segment_from_mask_pipe(
            params_template=params_template_seg,
            params=parse_key(params, "brain_segment_pipe"), space=space)

    else:
        print("Error, brain_segment_pipe or brain_old_segment_pipe\
            was not found in params, skipping")
        return seg_pipe

    seg_pipe.connect(
        data_preparation_pipe, 'outputnode.stereo_debiased_T1',
        brain_segment_pipe, 'inputnode.debiased_T1')

    seg_pipe.connect(restore_mask_T1, 'out_file',
                     brain_segment_pipe, 'inputnode.masked_debiased_T1')

    seg_pipe.connect(inputnode, 'indiv_params',
                     brain_segment_pipe, 'inputnode.indiv_params')

    # outputnode
    seg_pipe.connect(brain_segment_pipe, 'outputnode.segmented_file',
                     outputnode, 'stereo_segmented_brain_mask')

    seg_pipe.connect(brain_segment_pipe, 'outputnode.prob_csf',
                     outputnode, 'stereo_prob_csf')

    seg_pipe.connect(brain_segment_pipe, 'outputnode.prob_gm',
                     outputnode, 'stereo_prob_gm')

    seg_pipe.connect(brain_segment_pipe, 'outputnode.prob_wm',
                     outputnode, 'stereo_prob_wm')

    if pad and space == "native":

        pad_back(
            seg_pipe, data_preparation_pipe,
            brain_segment_pipe, "outputnode.segmented_file",
            outputnode, "native_segmented_brain_mask", params)

        pad_back(
            seg_pipe, data_preparation_pipe,
            brain_segment_pipe, "outputnode.prob_gm",
            outputnode, "native_prob_gm", params,
            inter_val="LIN")

        pad_back(
            seg_pipe, data_preparation_pipe,
            brain_segment_pipe, "outputnode.prob_wm",
            outputnode, "native_prob_wm", params,
            inter_val="LIN")

        pad_back(
            seg_pipe, data_preparation_pipe,
            brain_segment_pipe, "outputnode.prob_csf",
            outputnode, "native_prob_csf", params,
            inter_val="LIN")

    # ############################################## export 5tt

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
                                   outputnode, 'stereo_gen_5tt')

        if pad and space == "native":
            pad_back(
                seg_pipe, data_preparation_pipe,
                brain_segment_pipe, "outputnode.gen_5tt",
                outputnode, "native_gen_5tt", params)

    # ################################################### surface
    if "nii2mesh_brain_pipe" in params["brain_segment_pipe"]:

        nii2mesh_brain_pipe = create_nii2mesh_brain_pipe(
            params=parse_key(params["brain_segment_pipe"],
                             "nii2mesh_brain_pipe"))

        seg_pipe.connect(brain_segment_pipe, "outputnode.segmented_file",
                         nii2mesh_brain_pipe, 'inputnode.segmented_file')

        # outputnode
        seg_pipe.connect(nii2mesh_brain_pipe, "outputnode.wmgm_stl",
                         outputnode, 'wmgm_stl')

        seg_pipe.connect(nii2mesh_brain_pipe, "outputnode.wmgm_nii",
                         outputnode, 'stereo_wmgm_mask')

        if pad and space == "native":
            pad_back(
                seg_pipe, data_preparation_pipe,
                nii2mesh_brain_pipe, "outputnode.wmgm_nii",
                outputnode, "native_wmgm_mask", params)

    elif "IsoSurface_brain_pipe" in params["brain_segment_pipe"].keys():

        IsoSurface_brain_pipe = create_IsoSurface_brain_pipe(
            params=parse_key(params["brain_segment_pipe"],
                             "IsoSurface_brain_pipe"))

        seg_pipe.connect(brain_segment_pipe, "outputnode.segmented_file",
                         IsoSurface_brain_pipe, 'inputnode.segmented_file')

        # outputnode
        seg_pipe.connect(IsoSurface_brain_pipe, "outputnode.wmgm_stl",
                         outputnode, 'wmgm_stl')

        seg_pipe.connect(IsoSurface_brain_pipe, "outputnode.wmgm_nii",
                         outputnode, 'stereo_wmgm_mask')

        if pad and space == "native":
            pad_back(
                seg_pipe, data_preparation_pipe,
                IsoSurface_brain_pipe, "outputnode.wmgm_nii",
                outputnode, "native_wmgm_mask", params)

    return seg_pipe
