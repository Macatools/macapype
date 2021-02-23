"""
    Pipelines for brain extraction

"""
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from nipype.interfaces import ants
import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni

from ..nodes.extract_brain import AtlasBREX

from ..utils.utils_nodes import NodeParams, parse_key


def create_extract_pipe(params_template, params={}, name="extract_pipe"):
    """
    Description: Extract T1 brain using AtlasBrex

    Params:

    - norm_intensity (see `N4BiasFieldCorrection <https://nipype.readthedocs\
    .io/en/0.12.1/interfaces/generated/nipype.interfaces.ants.segmentation.\
    html#n4biasfieldcorrection>`_ for arguments)
    - atlas_brex (see :class:`AtlasBREX \
    <macapype.nodes.extract_brain.AtlasBREX>` for arguments) - also \
    available as :ref:`indiv_params <indiv_params>`

    Inputs:

        inputnode:

            restore_T1:
                preprocessed (debiased/denoised) T1 file name

            restore_T2:
                preprocessed (debiased/denoised)T2 file name

        arguments:

            params_template:
                dictionary of info about template

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "extract_pipe")

    Outputs:

        smooth_mask.out_file:
            Computed mask (after some smoothing)

    """

    # creating pipeline
    extract_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['restore_T1', 'restore_T2',
                                      "indiv_params"]),
        name='inputnode')

    # atlas_brex
    atlas_brex = NodeParams(AtlasBREX(),
                            params=parse_key(params, "atlas_brex"),
                            name='atlas_brex')

    extract_pipe.connect(inputnode, "restore_T1",
                         atlas_brex, 't1_restored_file')

    atlas_brex.inputs.NMT_file = params_template["template_head"]
    atlas_brex.inputs.NMT_SS_file = params_template["template_brain"]

    extract_pipe.connect(
            inputnode, ("indiv_params", parse_key, "atlas_brex"),
            atlas_brex, 'indiv_params')

    # mask_brex
    mask_brex = pe.Node(fsl.UnaryMaths(), name='mask_brex')
    mask_brex.inputs.operation = 'bin'

    extract_pipe.connect(atlas_brex, 'brain_file', mask_brex, 'in_file')

    # smooth_mask
    smooth_mask = pe.Node(fsl.UnaryMaths(), name='smooth_mask')
    smooth_mask.inputs.operation = "bin"
    smooth_mask.inputs.args = "-s 1 -thr 0.5 -bin"

    extract_pipe.connect(mask_brex, 'out_file', smooth_mask, 'in_file')

    # mult_T1
    mult_T1 = pe.Node(afni.Calc(), name='mult_T1')
    mult_T1.inputs.expr = "a*b"
    mult_T1.inputs.outputtype = 'NIFTI_GZ'

    extract_pipe.connect(inputnode, "restore_T1", mult_T1, 'in_file_a')
    extract_pipe.connect(smooth_mask, 'out_file', mult_T1, 'in_file_b')

    # mult_T2
    mult_T2 = pe.Node(afni.Calc(), name='mult_T2')
    mult_T2.inputs.expr = "a*b"
    mult_T2.inputs.outputtype = 'NIFTI_GZ'

    extract_pipe.connect(inputnode, 'restore_T2', mult_T2, 'in_file_a')
    extract_pipe.connect(smooth_mask, 'out_file', mult_T2, 'in_file_b')
    return extract_pipe


def create_extract_T1_pipe(params_template, params={},
                           name="extract_T1_pipe"):
    """
    Description: Extract T1 brain using AtlasBrex

    Params:

    - norm_intensity (see `N4BiasFieldCorrection <https://nipype.readthedocs.\
    io/en/0.12.1/interfaces/generated/nipype.interfaces.ants.segmentation.html\
    #n4biasfieldcorrection>`_ for arguments)
    - atlas_brex (see :class:`AtlasBREX \
    <macapype.nodes.extract_brain.AtlasBREX>` for arguments) - also available \
    as :ref:`indiv_params <indiv_params>`

    Inputs:

        inputnode:

            restore_T1:
                preprocessed (debiased/denoised) T1 file name

        arguments:

            params_template:
                dictionary of info about template

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "extract_pipe")

    Outputs:

        smooth_mask.out_file:
            Computed mask (after some smoothing)

    """

    # creating pipeline
    extract_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['restore_T1',
                                      "indiv_params"]),
        name='inputnode')

    # N4 intensity normalization with parameters from json
    norm_intensity = NodeParams(ants.N4BiasFieldCorrection(),
                                params=parse_key(params, "norm_intensity"),
                                name='norm_intensity')

    extract_pipe.connect(inputnode, 'restore_T1',
                         norm_intensity, "input_image")

    # atlas_brex
    atlas_brex = NodeParams(AtlasBREX(),
                            params=parse_key(params, "atlas_brex"),
                            name='atlas_brex')

    extract_pipe.connect(norm_intensity, "output_image",
                         atlas_brex, 't1_restored_file')

    atlas_brex.inputs.NMT_file = params_template["template_head"]
    atlas_brex.inputs.NMT_SS_file = params_template["template_brain"]

    extract_pipe.connect(
            inputnode, ("indiv_params", parse_key, "atlas_brex"),
            atlas_brex, 'indiv_params')

    # mask_brex
    mask_brex = pe.Node(fsl.UnaryMaths(), name='mask_brex')
    mask_brex.inputs.operation = 'bin'

    extract_pipe.connect(atlas_brex, 'brain_file', mask_brex, 'in_file')

    # smooth_mask
    smooth_mask = pe.Node(fsl.UnaryMaths(), name='smooth_mask')
    smooth_mask.inputs.operation = "bin"
    smooth_mask.inputs.args = "-s 1 -thr 0.5 -bin"

    extract_pipe.connect(mask_brex, 'out_file', smooth_mask, 'in_file')

    # mult_T1
    mult_T1 = pe.Node(afni.Calc(), name='mult_T1')
    mult_T1.inputs.expr = "a*b"
    mult_T1.inputs.outputtype = 'NIFTI_GZ'

    extract_pipe.connect(inputnode, 'restore_T1', mult_T1, 'in_file_a')
    extract_pipe.connect(smooth_mask, 'out_file', mult_T1, 'in_file_b')

    return extract_pipe
