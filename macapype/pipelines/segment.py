import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.spm as spm

from ..nodes.segment import AtroposN4, BinaryFillHoles

from ..utils.misc import get_elem, merge_3_elem_to_list
from ..utils.utils_spm import format_spm_priors
from ..utils.utils_nodes import NodeParams


def create_segment_atropos_pipe(params={}, name="segment_atropos_pipe"):
    """
    Description: Segmentation with ANTS atropos script

    Inputs:

        inputnode:
            brain_file: T1 image, after extraction and norm bin_norm_intensity

            gm_prior_file: grey matter tissue intensity file

            wm_prior_file: white matter tissue intensity file

            csf_prior_file: csf tissue intensity file

        arguments:
            params: dictionary of node sub-parameters (from a json file)

            name: pipeline name (default = "segment_atropos_pipe")

    Outputs:

        threshold_csf.out_file:
            csf tissue intensity mask in subject space
        threshold_gm.out_file:
            grey matter tissue intensity mask in subject space
        threshold_wm.out_file:
            white matter tissue intensity mask in subject space
    """
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
    seg_at = NodeParams(AtroposN4(), name='seg_at')

    if "Atropos" in params.keys():
        seg_at.load_inputs_from_dict(params["Atropos"])

    segment_pipe.connect(inputnode, "brain_file", seg_at, "brain_file")
    segment_pipe.connect(bin_norm_intensity, 'out_file',
                         seg_at, "brainmask_file")

    segment_pipe.connect(merge_3_elem, 'merged_list',
                         seg_at, "priors")

    # Threshold GM, WM and CSF
    thd_nodes = {}
    for i, tissue in enumerate(['csf', 'gm', 'wm']):
        tmp_node = NodeParams(fsl.Threshold(), name="threshold_" + tissue)

        if "threshold_" + tissue in params.keys():
            tmp_node.load_inputs_from_dict(params["threshold_" + tissue])

        segment_pipe.connect(seg_at, ('segmented_files', get_elem, i),
                             tmp_node, 'in_file')

        thd_nodes[tissue] = tmp_node

    return segment_pipe


def create_old_segment_pipe(params_template, params={},
                            name="old_segment_pipe"):
    """
    Description: Extract brain using tissues masks output by SPM's old_segment
        function:

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

            name: pipeline name (default = "old_segment_pipe")

    Outputs:

        fill_holes.out_file:
            filled mask after erode

        fill_holes_dil.out_file
            filled mask after dilate

        threshold_gm, threshold_wm, threshold_csf.out_file:
            resp grey matter, white matter, and csf after thresholding

    """
    # creating pipeline
    be_pipe = pe.Workflow(name=name)

    # Creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1']),
        name='inputnode'
    )

    # Segment in to 6 tissues
    segment = NodeParams(spm.Segment(), name="old_segment")

    if "segment" in params.keys():
        segment.load_inputs_from_dict(params["segment"])

    segment.tissue_prob_maps = format_spm_priors(
        [params_template["template_gm"], params_template["template_wm"],
         params_template["template_csf"]])

    be_pipe.connect(inputnode, 'T1', segment, 'data')

    # Threshold GM, WM and CSF
    thd_nodes = {}
    for tissue in ['gm', 'wm', 'csf']:

        tmp_node = NodeParams(fsl.Threshold(), name="threshold_" + tissue)

        if "threshold_" + tissue in params.keys():
            tmp_node.load_inputs_from_dict(params["threshold_" + tissue])

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
    dilate_mask = NodeParams(fsl.DilateImage(), name="dilate_mask")
    if "dilate_mask" in params.keys():
        dilate_mask.load_inputs_from_dict(params["dilate_mask"])

    dilate_mask.inputs.operation = "mean"  # Arbitrary operation
    be_pipe.connect(tissues_union, 'out_file', dilate_mask, 'in_file')

    # Eroding mask
    erode_mask = NodeParams(fsl.ErodeImage(), name="erode_mask")

    if "erode_mask" in params.keys():
        erode_mask.load_inputs_from_dict(params["erode_mask"])

    be_pipe.connect(tissues_union, 'out_file', erode_mask, 'in_file')

    # fill holes of erode_mask
    fill_holes = pe.Node(BinaryFillHoles(), name="fill_holes")
    be_pipe.connect(erode_mask, 'out_file', fill_holes, 'in_file')

    # fill holes of dilate_mask
    fill_holes_dil = pe.Node(BinaryFillHoles(), name="fill_holes_dil")
    be_pipe.connect(dilate_mask, 'out_file', fill_holes_dil, 'in_file')

    return be_pipe
