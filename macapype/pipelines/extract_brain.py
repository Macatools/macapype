
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni

from ..nodes.extract_brain import apply_atlasBREX


def create_brain_extraction_pipe(name="brain_extraction_pipe"):

    # creating pipeline
    brain_extraction_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['restore_T1', 'restore_T2']),
        name='inputnode')

    # atlas_brex
    atlas_brex = pe.Node(niu.Function(input_names=['t1_restored_file'],
                                      output_names=['brain_file'],
                                      function=apply_atlasBREX),
                         name='atlas_brex')

    brain_extraction_pipe.connect(inputnode, "restore_T1",
                                  atlas_brex, 't1_restored_file')

    # mask_brex
    mask_brex = pe.Node(fsl.UnaryMaths(), name='mask_brex')
    mask_brex.inputs.operation = 'bin'

    brain_extraction_pipe.connect(atlas_brex, 'brain_file',
                                  mask_brex, 'in_file')

    # smooth_mask
    smooth_mask = pe.Node(fsl.UnaryMaths(), name='smooth_mask')
    smooth_mask.inputs.operation = "bin"
    smooth_mask.inputs.args = "-s 1 -thr 0.5 -bin"

    brain_extraction_pipe.connect(mask_brex, 'out_file',
                                  smooth_mask, 'in_file')

    # mult_T1
    mult_T1 = pe.Node(afni.Calc(), name='mult_T1')
    mult_T1.inputs.expr = "a*b"
    mult_T1.inputs.outputtype = 'NIFTI_GZ'

    brain_extraction_pipe.connect(inputnode, "restore_T1",
                                  mult_T1, 'in_file_a')
    brain_extraction_pipe.connect(smooth_mask, 'out_file',
                                  mult_T1, 'in_file_b')

    # mult_T2
    mult_T2 = pe.Node(afni.Calc(), name='mult_T2')
    mult_T2.inputs.expr = "a*b"
    mult_T2.inputs.outputtype = 'NIFTI_GZ'

    brain_extraction_pipe.connect(inputnode, 'restore_T1',
                                  mult_T2, 'in_file_a')
    brain_extraction_pipe.connect(smooth_mask, 'out_file',
                                  mult_T2, 'in_file_b')
    return brain_extraction_pipe
