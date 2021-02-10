
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe
from nipype.interfaces import ants
from nipype.interfaces import fsl

from ..utils.utils_nodes import NodeParams

from macapype.nodes.correct_bias import T1xT2BiasFieldCorrection
from macapype.nodes.register import IterREGBET

from .prepare import (create_short_preparation_pipe,
                      create_long_multi_preparation_pipe,
                      create_long_single_preparation_pipe,
                      create_short_preparation_T1_pipe)

from .segment import (create_old_segment_pipe,
                      create_segment_atropos_pipe)

from .correct_bias import (create_masked_correct_bias_pipe,
                           create_correct_bias_pipe)

from .register import create_register_NMT_pipe

from .extract_brain import (create_extract_pipe,
                            create_extract_T1_pipe)

from .surface import create_nii_to_mesh_pipe

from macapype.utils.misc import gunzip, parse_key, list_input_files


###############################################################################
# SPM based segmentation (from: Régis Trapeau) (-soft SPM or SPM12)
def create_full_spm_subpipes(
        params_template, params={}, name='full_spm_subpipes'):
    """ Description: SPM based segmentation pipeline from T1w and T2w images

        - data_preparation_pipe:
            - avg_align
            - deoblique,
            - reorient if needed
            - bet_crop (brain extraction and crop) -> mask
            - denoise
        - T1xT2BiasFieldCorrection using mask -> debias
        - IterREGBET -> registration to template file
        - old_segment_pipe

    Inputs:

        inputnode:
            list_T1: T1 file names
            list_T2: T2 file names

            indiv_params (opt): dict with individuals parameters for some nodes


        arguments:
            params_template: dict of template files containing brain_template
            and priors (list of template based segmented tissues)

            params: dictionary of node sub-parameters (from a json file)

            name: pipeline name (default = "full_spm_subpipes")

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

    # preprocessing
    if 'short_preparation_pipe' in params.keys():
        #assert 'bet_crop' in parse_key(params, "short_preparation_pipe"),\
            "This version should contains betcrop in params.json"

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

    if 'bet_crop' in parse_key(params, "short_preparation_pipe"):
        seg_pipe.connect(data_preparation_pipe, 'bet_crop.mask_file',
                         debias, 'b')
    else:
        debias.inputs.bet = 1

    # Iterative registration to the INIA19 template
    reg = NodeParams(IterREGBET(),
                     params=parse_key(params, "reg"),
                     name='reg')

    reg.inputs.refb_file = params_template["template_brain"]

    seg_pipe.connect(debias, 't1_debiased_file', reg, 'inw_file')
    seg_pipe.connect(debias, 't1_debiased_brain_file',
                     reg, 'inb_file')

    seg_pipe.connect(
        inputnode, ('indiv_params', parse_key, "reg"),
        reg, 'indiv_params')

    # Compute brain mask using old_segment of SPM and postprocessing on
    # tissues' masks
    if "old_segment_pipe" in params.keys():

        old_segment_pipe = create_old_segment_pipe(
            params_template, params=parse_key(params, "old_segment_pipe"))

        seg_pipe.connect(reg, ('warp_file', gunzip),
                         old_segment_pipe, 'inputnode.T1')

        seg_pipe.connect(
            inputnode, 'indiv_params',
            old_segment_pipe, 'inputnode.indiv_params')

    return seg_pipe


###############################################################################
# SPM based, but only T1 is available (-soft SPM_T1)
def create_full_T1_spm_subpipes(
        params_template, params={}, name='full_T1_spm_subpipes'):
    """ Description: SPM based segmentation pipeline from T1w image only.
        This is fact the same as create_full_spm_subpipes, where T2 is
        replaced by T1

        - data_preparation_pipe:
            - avg_align
            - deoblique,
            - reorient if needed
            - bet_crop (brain extraction and crop) -> mask
            - denoise
        - T1xT2BiasFieldCorrection using mask -> debias
        - IterREGBET -> registration to template file
        - old_segment_pipe

    Inputs:

        inputnode:
            list_T1: T1 file names

            indiv_params (opt): dict with individuals parameters for some nodes


        arguments:
            params_template: dict of template files containing brain_template
            and priors (list of template based segmented tissues)

            params: dictionary of node sub-parameters (from a json file)

            name: pipeline name (default = "full_spm_subpipes")

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
        niu.IdentityInterface(fields=['list_T1', 'indiv_params']),
        name='inputnode'
    )

    # preprocessing
    data_preparation_pipe = create_short_preparation_pipe(
        params=parse_key(params, "short_preparation_pipe"))

    seg_pipe.connect(inputnode, 'list_T1',
                     data_preparation_pipe, 'inputnode.list_T1')
    seg_pipe.connect(inputnode, 'list_T1',
                     data_preparation_pipe, 'inputnode.list_T2')
    seg_pipe.connect(inputnode, 'indiv_params',
                     data_preparation_pipe, 'inputnode.indiv_params')

    # Bias correction of cropped images
    debias = NodeParams(T1xT2BiasFieldCorrection(),
                        params=parse_key(params, "debias"),
                        name='debias')

    seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                     debias, 't1_file')
    seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                     debias, 't2_file')
    seg_pipe.connect(data_preparation_pipe, 'bet_crop.mask_file',
                     debias, 'b')
    seg_pipe.connect(
        inputnode, ('indiv_params', parse_key, "debias"),
        debias, 'indiv_params')

    # Iterative registration to the INIA19 template
    reg = NodeParams(IterREGBET(),
                     params=parse_key(params, "reg"),
                     name='reg')
    reg.inputs.refb_file = params_template["template_brain"]
    seg_pipe.connect(debias, 't1_debiased_file', reg, 'inw_file')
    seg_pipe.connect(debias, 't1_debiased_brain_file',
                     reg, 'inb_file')
    seg_pipe.connect(
        inputnode, ('indiv_params', parse_key, "reg"),
        reg, 'indiv_params')

    # Subject to _template (ants)
    nonlin_reg = NodeParams(ants.RegistrationSynQuick(),
                            params=parse_key(params, "nonlin_reg"),
                            name='nonlin_reg')
    nonlin_reg.inputs.fixed_image = params_template["template_brain"]
    seg_pipe.connect(reg, "warp_file", nonlin_reg, "moving_image")

    # Transform T1 (fsl)
    transform_msk = NodeParams(fsl.ApplyXFM(),
                               params=parse_key(params, "transform_mask"),
                               name='transform_others')
    seg_pipe.connect(nonlin_reg, "out_matrix", transform_msk, "in_matrix_file")
    seg_pipe.connect(debias, "debiased_mask_file", transform_msk, "in_file")
    seg_pipe.connect(debias, "t1_debiased_file", transform_msk, "reference")

    # Compute brain mask using old_segment of SPM and postprocessing on
    # tissues' masks
    if "old_segment_pipe" in params.keys():

        old_segment_pipe = create_old_segment_pipe(
            params_template, params=parse_key(params, "old_segment_pipe"))

        seg_pipe.connect(nonlin_reg, ('warped_image', gunzip),
                         old_segment_pipe, 'inputnode.T1')

        seg_pipe.connect(
            inputnode, 'indiv_params',
            old_segment_pipe, 'inputnode.indiv_params')

    return seg_pipe

###############################################################################
# ANTS based segmentation (from Kepkee Loh / Julien Sein)


def create_brain_extraction_pipe(params_template, params={},
                                 name="brain_extraction_pipe"):
    """ Description: ANTS based segmentation pipeline using T1w and T2w images

    - correct_bias

    - denoise

    - extract_brain

    Inputs:

        inputnode:
            preproc_T1: preprocessed T1 file
            preproc_T2: preprocessed T2 file

            indiv_params (opt): dict with individuals parameters for some nodes


        arguments:
            params_template: dictionary of template files
            params: dictionary of node sub-parameters (from a json file)
            name: pipeline name (default = "full_segment_pipe")

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

    brain_extraction_pipe.connect(correct_bias_pipe, "restore_T1.out_file",
                                  extract_pipe, "inputnode.restore_T1")
    brain_extraction_pipe.connect(correct_bias_pipe, "restore_T2.out_file",
                                  extract_pipe, "inputnode.restore_T2")
    brain_extraction_pipe.connect(inputnode, "indiv_params",
                                  extract_pipe, "inputnode.indiv_params")
    return brain_extraction_pipe


def create_brain_segment_from_mask_pipe(
        params_template, params={}, name="brain_segment_from_mask_pipe"):
    """ Description: Segment T1 (using T2 for bias correction) and a previously
    computed mask with NMT Atlas and atropos segment.

    - debias T1xT2 in mask only (masked_correct_bias_pipe)

    - NMT align (after N4Debias)

    - Atropos segment

    Inputs:

        inputnode:
            preproc_T1: preprocessed T1 file name

            preproc_T2: preprocessed T2 file name

            brain_mask: a mask computed for the same T1/T2 images

            indiv_params (opt): dict with individuals parameters for some nodes


        arguments:
            params_template: dictionary of template files

            params: dictionary of node sub-parameters (from a json file)

            name: pipeline name (default = "full_segment_pipe")

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
        params=parse_key(params, "register_NMT_pipe"))

    brain_segment_pipe.connect(
        masked_correct_bias_pipe, 'restore_mask_T1.out_file',
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


# (-soft ANTS)
def create_full_ants_subpipes(
        params_template, params={}, name="full_ants_subpipes"):
    """Description: Segment T1 (using T2 for bias correction) .

    new version (as it is now)
    - brain preproc (avg and align, reorient of specified cropping from T1xT2BET, bet is optional) # noqa
    - brain extraction (see create_brain_extraction_pipe):
        - correct_bias
        - denoise
        - extract_brain
    - brain segment from mask (see create_brain_segment_from_mask_pipe):
        - denoise pipe
        - debias pipe
        - NMT align (after N4Debias)
        - Atropos segment

    Inputs:

        inputnode:
            list_T1: preprocessed T1 file name

            list_T2: preprocessed T2 file name

            indiv_params (opt): dict with individuals parameters for some nodes

        arguments:
            params_template: dictionary of template files

            params: dictionary of node sub-parameters (from a json file)

            name: pipeline name (default = "full_segment_pipe")

    Outputs:

    """
    # creating pipeline
    seg_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['list_T1', 'list_T2', 'indiv_params']),
        name='inputnode'
    )

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

    brain_segment_pipe = create_brain_segment_from_mask_pipe(
        params_template=params_template,
        params=parse_key(params, "brain_segment_pipe"))

    seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T1',
                     brain_segment_pipe, 'inputnode.preproc_T1')
    seg_pipe.connect(data_preparation_pipe, 'outputnode.preproc_T2',
                     brain_segment_pipe, 'inputnode.preproc_T2')
    seg_pipe.connect(brain_extraction_pipe,
                     "extract_pipe.smooth_mask.out_file",
                     brain_segment_pipe, "inputnode.brain_mask")
    seg_pipe.connect(inputnode, 'indiv_params',
                     brain_segment_pipe, 'inputnode.indiv_params')

    if 'nii_to_mesh_pipe' not in params.keys():
        return seg_pipe

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

    seg_pipe.connect(brain_segment_pipe,
                     'register_NMT_pipe.NMT_subject_align.inv_transfo_file',
                     nii_to_mesh_pipe, 'inputnode.inv_transfo_file')

    seg_pipe.connect(brain_segment_pipe,
                     'register_NMT_pipe.NMT_subject_align.aff_file',
                     nii_to_mesh_pipe, 'inputnode.aff_file')

    seg_pipe.connect(brain_segment_pipe,
                     'segment_atropos_pipe.seg_at.segmented_file',
                     nii_to_mesh_pipe, "inputnode.segmented_file")

    return seg_pipe

###############################################################################
# ANTS based segmentation for adrien baboons (T1 without T2)
###############################################################################


# same as above, but replacing biascorrection with N4biascorrection
# in brain extraction and brain segmentation
def create_brain_extraction_T1_pipe(params_template, params={},
                                    name="brain_extraction_T1_pipe"):
    """ Description: Brain extraction with only T1 images.

    - N4biascorrection (replacing T2 bias correction with N4)

    - extract_brain using atlasbrex

    Inputs:

        inputnode:
            preproc_T1: preprocessed T1 file
            indiv_params (opt): dict with individuals parameters for some nodes


        arguments:
            params_template: dictionary of template files
            params: dictionary of node sub-parameters (from a json file)
            name: pipeline name (default = "full_segment_pipe")

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
    """ Description: Segment T1 (using T2 for bias correction) and a previously
    computed mask with NMT Atlas and atropos segment.

    - debias T1xT2 in mask only (masked_correct_bias_pipe)

    - NMT align (after N4Debias)

    - Atropos segment

    Inputs:

        inputnode:
            preproc_T1: preprocessed T1 file name

            brain_mask: a mask computed for the same T1/T2 images

            indiv_params (opt): dict with individuals parameters for some nodes


        arguments:
            params_template: dictionary of template files

            params: dictionary of node sub-parameters (from a json file)

            name: pipeline name (default = "full_segment_pipe")

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


# -soft ANTS_T1
def create_full_T1_ants_subpipes(
    params_template, params={},
        name="full_T1_ants_subpipes"):
    """Description: Segment T1 (with no T2).

    - brain preproc (short_prepration pipe - try betcrop with the same file,
    includes denoising from ants)
    - Perform N4biascorrection with defined parameters.
    - brain extraction (see create_brain_extraction_pipe):
        - correct_bias
        - denoise
        - extract_brain
    - brain segment from mask (see create_brain_segment_from_mask_pipe):
        - denoise pipe
        - debias pipe
        - NMT align (after N4Debias)
        - Atropos segment

    Inputs:

        inputnode:
            list_T1: preprocessed T1 file name

            indiv_params (opt): dict with individuals parameters for some nodes

        arguments:
            params_template: dictionary of template files

            params: dictionary of node sub-parameters (from a json file)

            name: pipeline name (default = "full_segment_pipe")

    Outputs:

    """
    # creating pipeline
    seg_pipe = pe.Workflow(name=name)

    # Creating input node (grab only T1 files)
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['list_T1', 'indiv_params']),
        name='inputnode'
    )

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

    return seg_pipe
