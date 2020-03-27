
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.spm as spm

from ..nodes.segment import wrap_antsAtroposN4_dirty

from .denoise import create_denoised_pipe
from .correct_bias import create_masked_correct_bias_pipe
from .register import create_register_NMT_pipe

# from ..nodes.binary_fill_holes import apply_binary_fill_holes_dirty
from ..nodes.binary_fill_holes import BinaryFillHoles

def create_segment_atropos_pipe(dimension, numberOfClasses,
                                name="segment_atropos_pipe"):

    # creating pipeline
    segment_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=["brain_file", "gm_prior_file", "wm_prior_file",
                    "csf_prior_file"]),
        name='inputnode')

    # bin_norm_intensity (a cheat from Kepkee if I understood well!)
    bin_norm_intensity = pe.Node(fsl.UnaryMaths(), name="bin_norm_intensity")
    bin_norm_intensity.inputs.operation = "bin"

    segment_pipe.connect(inputnode, "brain_file",
                         bin_norm_intensity, "in_file")

    # STEP 3: ants Atropos
    # Atropos
    seg_at = pe.Node(niu.Function(
        input_names=["dimension", "brain_file", "brainmask_file",
                     "numberOfClasses", "ex_prior1", "ex_prior2", "ex_prior3"],
        output_names=["out_files", "seg_file", "seg_post1_file",
                      "seg_post2_file", "seg_post3_file"],
        function=wrap_antsAtroposN4_dirty), name='seg_at')

    seg_at.inputs.dimension = dimension
    seg_at.inputs.numberOfClasses = numberOfClasses

    segment_pipe.connect(inputnode, 'brain_file', seg_at, "brain_file")
    segment_pipe.connect(bin_norm_intensity, 'out_file',
                         seg_at, "brainmask_file")

    # TODO
    # was like this before (1 -> csf, 2 -> gm, 3 -> wm, to check)
    segment_pipe.connect(inputnode, 'csf_prior_file', seg_at, "ex_prior1")
    segment_pipe.connect(inputnode, 'gm_prior_file', seg_at, "ex_prior2")
    segment_pipe.connect(inputnode, 'wm_prior_file', seg_at, "ex_prior3")

    return segment_pipe


def create_old_segment_extraction_pipe(priors,
                                       name="old_segment_extraction_pipe"):
    """ Extract brain using tissues masks output by SPM's old_segment function

    1 - Segment the T1 using given priors;
    2 - Threshold GM, WM and CSF maps;
    3 - Compute union of those 3 tissues;
    4 - Apply morphological opening on the union mask
    5 - Fill holes

    Inputs
    ======
    T1: T1 file name
    seg_priors: list of file names

    Outputs
    --------

    """
    # creating pipeline
    be_pipe = pe.Workflow(name=name)

    # Creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1']),
        name='inputnode'
    )

    # Segment in to 6 tissues
    segment = pe.Node(spm.Segment(), name="old_segment")
    segment.inputs.gm_output_type = [False, False, True]
    segment.inputs.wm_output_type = [False, False, True]
    segment.inputs.csf_output_type = [False, False, True]
    segment.tissue_prob_maps = priors
    be_pipe.connect(inputnode, 'T1', segment, 'data')

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
    be_pipe.connect(thd_nodes['csf'], 'out_file',
                    tissues_union, 'operand_file')

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

    fill_holes = pe.Node(BinaryFillHoles(), name="fill_holes")
    be_pipe.connect(erode_mask, 'out_file', fill_holes, 'in_file')

    fill_holes_dil = pe.Node(BinaryFillHoles(), name="fill_holes_dil")
    be_pipe.connect(dilate_mask, 'out_file', fill_holes_dil, 'in_file')

    return be_pipe
