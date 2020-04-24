"""
    Pipelines for brain extraction

"""
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni

from ..nodes.extract_brain import AtlasBREX


def create_extract_pipe(params_template, params={}, name="extract_pipe"):
    """
    Description: Extract T1 brain using AtlasBrex

    Inputs:

        inputnode:
            restore_T1: preprocessed (debiased/denoised) T1 file name

            restore_T1: preprocessed (debiased/denoised)T2 file name

        arguments:
            params_template: dictionary of info about template

            params: dictionary of node sub-parameters (from a json file)

            name: pipeline name (default = "extract_pipe")

    Outputs:

        smooth_mask.out_file:
            Computed mask (after some smoothing)

    """

    # creating pipeline
    extract_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['restore_T1', 'restore_T2']),
        name='inputnode')

    # atlas_brex
    if "atlas_brex" in params.keys():
        f = params["atlas_brex"]["f"]
        reg = params["atlas_brex"]["reg"]
        wrp = params["atlas_brex"]["wrp"]
        msk = params["atlas_brex"]["msk"]
        # wrp = params["atlas_brex"]["wrp"]
    else:
        f = 0.5
        reg = 1
        wrp = "10,10,10"
        msk = "a,0,0"
        # wrp = "1"

    atlas_brex = pe.Node(AtlasBREX(), name='atlas_brex')

    extract_pipe.connect(inputnode, "restore_T1",
                         atlas_brex, 't1_restored_file')

    atlas_brex.inputs.NMT_file = params_template["template_head"]
    atlas_brex.inputs.NMT_SS_file = params_template["template_brain"]
    atlas_brex.inputs.f = f
    atlas_brex.inputs.reg = reg
    atlas_brex.inputs.wrp = wrp
    atlas_brex.inputs.msk = msk
    # atlas_brex.inputs.wrp = wrp

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

    extract_pipe.connect(inputnode, 'restore_T1', mult_T2, 'in_file_a')
    extract_pipe.connect(smooth_mask, 'out_file', mult_T2, 'in_file_b')
    return extract_pipe
