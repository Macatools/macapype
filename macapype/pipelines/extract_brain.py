"""
    TODO :p

"""
import os.path as op

from scipy.ndimage import binary_fill_holes

import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni
import nipype.interfaces.spm as spm

from ..nodes.binary_fill_holes import apply_binary_fill_holes_dirty #BinaryFillHoles
from ..nodes.extract_brain import AtlasBREX
#from ..nodes.extract_brain import apply_atlasBREX


def create_brain_extraction_pipe(script_atlas_BREX, NMT_file, NMT_SS_file,
                                 f= 0.5, reg=1, w="10,10,10", msk="a,0,0",
                                 name="brain_extraction_pipe"):

    # creating pipeline
    brain_extraction_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['restore_T1', 'restore_T2']),
        name='inputnode')

    # atlas_brex
    atlas_brex = pe.Node(AtlasBREX(),name='atlas_brex')

    brain_extraction_pipe.connect(inputnode, "restore_T1",
                                  atlas_brex, 't1_restored_file')

    atlas_brex.inputs.script_atlas_BREX = script_atlas_BREX
    atlas_brex.inputs.NMT_file = NMT_file
    atlas_brex.inputs.NMT_SS_file = NMT_SS_file
    atlas_brex.inputs.f = f
    atlas_brex.inputs.reg = reg
    atlas_brex.inputs.w = w
    atlas_brex.inputs.msk = msk

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


def create_old_segment_extraction_pipe(name="old_segment_exctraction_pipe"):
    """ Extract brain using tissues masks outputed by SPM's old_segment function
    
    1 - Segment the T1 using given priors;
    2 - Threshold GM, WM and CSF maps;
    3 - Compute union of those 3 tissues;
    4 - Apply morphological opening on the union mask
    5 - Fill holes

    Inputs
    ---------
    T1: T1 file name
    seg_priors: list of file names
    
    Outputs
    --------
    
    """

    # creating pipeline
    be_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1', 'seg_priors']),
        name='inputnode'
    )
    
    # Segment in to 6 tissues
    segment = pe.Node(spm.Segment(), name="old_segment")
    segment.inputs.gm_output_type = [False,False,True]
    segment.inputs.wm_output_type = [False,False,True]
    segment.inputs.csf_output_type = [False,False,True]
    be_pipe.connect(inputnode, 'T1', segment, 'data')
    be_pipe.connect(inputnode, 'seg_priors', segment, 'tissue_prob_maps')

    # Threshold GM, WM and CSF
    thd_nodes = {}
    for tissue in ['gm', 'wm', 'csf']:
        tmp_node = pe.Node(fsl.Threshold(), name="threshold_" + tissue)
        tmp_node.inputs.thresh = 0.05
        be_pipe.connect(
            segment, 'native_' + tissue + '_image', 
            tmp_node, 'in_file'
        )
        thd_nodes[tissue] = tmp_node

    # Compute union of the 3 tissues
    # Done with 2 fslmaths as it seems to hard to do it 
    wmgm_union = pe.Node(fsl.BinaryMaths(), name="wmgm_union")
    wmgm_union.inputs.operation = "add"
    be_pipe.connect(thd_nodes['gm'], 'out_file', wmgm_union, 'in_file')
    be_pipe.connect(thd_nodes['wm'], 'out_file', wmgm_union, 'operand_file')

    tissues_union = pe.Node(fsl.BinaryMaths(), name="tissues_union")
    tissues_union.inputs.operation = "add"
    be_pipe.connect(wmgm_union, 'out_file', tissues_union, 'in_file')
    be_pipe.connect(thd_nodes['csf'], 'out_file', tissues_union, 'operand_file')
    
    # Opening
    opening_shape = "sphere"
    opening_size = 2
    dilate_mask = pe.Node(fsl.DilateImage(), name="dilate_mask")
    # Arbitrary operation
    dilate_mask.inputs.operation = "mean"
    dilate_mask.inputs.kernel_shape = opening_shape
    dilate_mask.inputs.kernel_size = opening_size
    be_pipe.connect(tissues_union, 'out_file', dilate_mask, 'in_file')

    erode_mask = pe.Node(fsl.ErodeImage(), name="erode_mask")
    erode_mask.inputs.kernel_shape = opening_shape
    erode_mask.inputs.kernel_size = opening_size
    be_pipe.connect(dilate_mask, 'out_file', erode_mask, 'in_file')

    # # Holes filling on open image
    # fill_holes = pe.Node(fsl.BinaryMaths(), name="fill_holes")
    # be_pipe.connect(erode_mask, 'out_file', fill_holes, 'in_file')
    #
    # fill_holes_dil = pe.Node(fsl.BinaryMaths(), name="fill_holes_dil")
    # be_pipe.connect(dilate_mask, 'out_file', fill_holes_dil, 'in_file')
    
    # Temporary dirty version
    # FIXME: the clean version doesn't work
    fill_holes = pe.Node(
        niu.Function(input_names=["in_file"],
                     output_names=["out_file"],
                     function=apply_binary_fill_holes_dirty),
        name="fill_holes"
    )
    be_pipe.connect(erode_mask, 'out_file', fill_holes, 'in_file')

    fill_holes_dil = pe.Node(
        niu.Function(input_names=["in_file"],
                     output_names=["out_file"],
                     function=apply_binary_fill_holes_dirty),
        name="fill_holes_dil"
    )
    be_pipe.connect(dilate_mask, 'out_file', fill_holes_dil, 'in_file')
    
    return be_pipe

