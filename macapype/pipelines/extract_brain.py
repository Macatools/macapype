"""
    Pipelines for brain extraction

"""
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl

from ..nodes.extract_brain import AtlasBREX, HDBET, Bet4Animal

from ..utils.utils_nodes import NodeParams, parse_key


def create_extract_pipe(params_template, params={},
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

    outputnode = pe.Node(niu.IdentityInterface(fields=['mask_file']),
                         name="outputnode")

    # smooth before brex
    if "smooth" in params.keys():

        smooth = NodeParams(fsl.utils.Smooth(),
                            params=parse_key(params, "smooth"),
                            name='smooth')

        extract_pipe.connect(inputnode, 'restore_T1',
                             smooth, 'in_file')

    if "bet4animal" in params:
        bet4animal = NodeParams(
            Bet4Animal(),
            params=parse_key(params, "bet4animal"),
            name='bet4animal')

        if "smooth" in params.keys():
            extract_pipe.connect(
                smooth, 'smoothed_file',
                bet4animal, 'in_file')
        else:

            extract_pipe.connect(
                inputnode, 'restore_T1',
                bet4animal, 'in_file')

        extract_pipe.connect(
                inputnode, ("indiv_params", parse_key, "bet4animal"),
                bet4animal, 'indiv_params')

        # outputnode
        extract_pipe.connect(bet4animal, 'mask_file', outputnode, 'mask_file')

    elif "hdbet" in params.keys():
        hdbet = NodeParams(HDBET(),
                           params=parse_key(params, "hdbet"),
                           name='hdbet')

        if "smooth" in params.keys():
            extract_pipe.connect(
                smooth, 'smoothed_file',
                hdbet, 'in_file')
        else:

            extract_pipe.connect(
                inputnode, 'restore_T1',
                hdbet, 'in_file')

        extract_pipe.connect(
                inputnode, ("indiv_params", parse_key, "atlas_brex"),
                hdbet, 'indiv_params')

        # outputnode
        extract_pipe.connect(hdbet, 'mask_file', outputnode, 'mask_file')
    else:

        # atlas_brex
        atlas_brex = NodeParams(
            AtlasBREX(),
            params=parse_key(params, "atlas_brex"),
            name='atlas_brex')

        if "smooth" in params.keys():
            extract_pipe.connect(smooth, 'smoothed_file',
                                 atlas_brex, 't1_restored_file')
        else:

            extract_pipe.connect(inputnode, 'restore_T1',
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

        # outputnode
        extract_pipe.connect(smooth_mask, 'out_file', outputnode, 'mask_file')

    return extract_pipe
