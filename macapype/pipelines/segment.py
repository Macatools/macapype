
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.spm as spm
import nipype.interfaces.afni as afni

from ..nodes.segment import AtroposN4

# from ..nodes.binary_fill_holes import apply_binary_fill_holes_dirty
from ..nodes.binary_fill_holes import BinaryFillHoles

from ..utils.misc import get_elem, merge_3_elem_to_list


def create_segment_atropos_pipe(params = {},
                                name="segment_atropos_pipe"):

    # creating pipeline
    segment_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=["brain_file", "gm_prior_file", "wm_prior_file",
                    "csf_prior_file"]),
        name='inputnode')

    # Adding force deoblique before norm and atropos (special for cerimed file)
    deoblique = pe.Node(afni.Refit(deoblique=True), name="deoblique")

    segment_pipe.connect(inputnode, "brain_file",
                         deoblique, "in_file")

    # bin_norm_intensity (a cheat from Kepkee if I understood well!)
    bin_norm_intensity = pe.Node(fsl.UnaryMaths(), name="bin_norm_intensity")
    bin_norm_intensity.inputs.operation = "bin"

    segment_pipe.connect(deoblique, "out_file",
                         bin_norm_intensity, "in_file")

    # merging priors as a list
    merge_3_elem = pe.Node(niu.Function(
        input_names=['elem1', 'elem2', 'elem3'],
        output_names=['merged_list'],
        function=merge_3_elem_to_list), name='merge_3_elem')

    # was like this before (1 -> csf, 2 -> gm, 3 -> wm, to check)
    segment_pipe.connect(inputnode, 'csf_prior_file', merge_3_elem, "elem1")
    segment_pipe.connect(inputnode, 'gm_prior_file', merge_3_elem, "elem2")
    segment_pipe.connect(inputnode, 'wm_prior_file', merge_3_elem, "elem3")

    # Atropos
    if "Atropos" in params.keys():
        dimension = params["Atropos"]["dimension"]
        numberOfClasses = params["Atropos"]["numberOfClasses"]
    else:
        dimension=3
        numberOfClasses=3

    seg_at = pe.Node(AtroposN4(), name='seg_at')

    seg_at.inputs.dimension = dimension
    seg_at.inputs.numberOfClasses = numberOfClasses

    segment_pipe.connect(deoblique, "out_file", seg_at, "brain_file")
    segment_pipe.connect(bin_norm_intensity, 'out_file',
                         seg_at, "brainmask_file")

    segment_pipe.connect(merge_3_elem, 'merged_list',
                         seg_at, "priors")

    # Threshold GM, WM and CSF
    thd_nodes = {}
    for i, tissue in enumerate(['csf', 'gm', 'wm']):
        tmp_node = pe.Node(fsl.Threshold(), name="threshold_" + tissue)
        tmp_node.inputs.thresh = 0.05
        segment_pipe.connect(seg_at, ('segmented_files', get_elem, i),
                             tmp_node, 'in_file')

        thd_nodes[tissue] = tmp_node

    return segment_pipe


def create_old_segment_pipe(priors, params = {}, name="old_segment_pipe"):
    """
    Description:
        Extract brain using tissues masks output by SPM's old_segment function:

        - Segment the T1 using given priors;
        - Threshold GM, WM and CSF maps;
        - Compute union of those 3 tissues;
        - Apply morphological opening on the union mask
        - Fill holes

    Inputs:

        inputnode:
            T1: T1 file name

        arguments:
            priors: list of file names

            params: dictionary of node sub-parameters (from a json file)

    Outputs:

        fill_holes.out_file:
                filled mask after erode

        fill_holes_dil.out_file
            filled mask after dilate

    """
    # creating pipeline
    be_pipe = pe.Workflow(name=name)

    # Creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1']),
        name='inputnode'
    )

    # Segment in to 6 tissues
    if "segment" in params.keys():
        gm_output_type = params["segment"]["gm_output_type"]
        wm_output_type = params["segment"]["wm_output_type"]
        csf_output_type = params["segment"]["csf_output_type"]
    else:
        gm_output_type = [False, False, True]
        wm_output_type = [False, False, True]
        csf_output_type = [False, False, True]

    segment = pe.Node(spm.Segment(), name="old_segment")
    segment.inputs.gm_output_type = gm_output_type
    segment.inputs.wm_output_type = wm_output_type
    segment.inputs.csf_output_type = csf_output_type
    segment.tissue_prob_maps = priors
    be_pipe.connect(inputnode, 'T1', segment, 'data')

    # Threshold GM, WM and CSF
    thd_nodes = {}
    for tissue in ['gm', 'wm', 'csf']:

        if "threshold_" + tissue in params.keys():
            thresh = params["threshold_" + tissue]["thresh"]
        else:
            thresh = 0.05

        tmp_node = pe.Node(fsl.Threshold(), name="threshold_" + tissue)
        tmp_node.inputs.thresh = thresh

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
    if "dilate_mask" in params.keys():
        opening_shape = params["dilate_mask"]["opening_shape"]
        opening_size = params["dilate_mask"]["opening_size"]

    else:
        opening_shape = "sphere"
        opening_size = 2

    dilate_mask = pe.Node(fsl.DilateImage(), name="dilate_mask")
    # Arbitrary operation
    dilate_mask.inputs.operation = "mean"
    dilate_mask.inputs.kernel_shape = opening_shape
    dilate_mask.inputs.kernel_size = opening_size
    be_pipe.connect(tissues_union, 'out_file', dilate_mask, 'in_file')

    # Eroding
    if "erode_mask" in params.keys():
        opening_shape = params["erode_mask"]["opening_shape"]
        opening_size = params["erode_mask"]["opening_size"]

    else:
        opening_shape = "sphere"
        opening_size = 2

    erode_mask = pe.Node(fsl.ErodeImage(), name="erode_mask")
    erode_mask.inputs.kernel_shape = opening_shape
    erode_mask.inputs.kernel_size = opening_size
    be_pipe.connect(dilate_mask, 'out_file', erode_mask, 'in_file')

    # fill holes of erode_mask
    fill_holes = pe.Node(BinaryFillHoles(), name="fill_holes")
    be_pipe.connect(erode_mask, 'out_file', fill_holes, 'in_file')

    # fill holes of dilate_mask
    fill_holes_dil = pe.Node(BinaryFillHoles(), name="fill_holes_dil")
    be_pipe.connect(dilate_mask, 'out_file', fill_holes_dil, 'in_file')

    return be_pipe
