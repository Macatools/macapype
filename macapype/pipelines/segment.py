import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.spm as spm

from ..nodes.segment import AtroposN4, BinaryFillHoles, merge_masks

from ..utils.misc import (gunzip, get_elem, merge_3_elem_to_list,
                          split_indexed_mask)
from ..utils.utils_nodes import NodeParams, parse_key
from ..utils.utils_spm import set_spm


def create_segment_atropos_seg_pipe(params={}, name="segment_atropos_pipe"):
    """
    Description: Segmentation with ANTS atropos script using seg file

    Params:
        - Atropos (see :class:`AtroposN4 <macapype.nodes.segment.AtroposN4>`)
        - threshold_gm, threshold_wm, threshold_csf (see `Threshold \
        <https://nipype.readthedocs.io/en/0.12.1/interfaces/generated/nipype.\
        interfaces.fsl.maths.html#threshold>`_ for arguments)

    Inputs:

        inputnode:
            brain_file: T1 image, after extraction and norm bin_norm_intensity

            seg_file: indexed  with all tissues as index file

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
            fields=["brain_file", "seg_file"]),
        name='inputnode')

    # bin_norm_intensity (a cheat from Kepkee if I understood well!)
    bin_norm_intensity = pe.Node(fsl.UnaryMaths(), name="bin_norm_intensity")
    bin_norm_intensity.inputs.operation = "bin"

    segment_pipe.connect(inputnode, "brain_file",
                         bin_norm_intensity, "in_file")

    # merging priors as a list
    split_seg = pe.Node(niu.Function(
        input_names=['nii_file'],
        output_names=['list_split_files'],
        function=split_indexed_mask), name='split_seg')

    segment_pipe.connect(inputnode, 'seg_file', split_seg, "nii_file")

    # Atropos
    seg_at = NodeParams(AtroposN4(),
                        params=parse_key(params, "Atropos"),
                        name='seg_at')

    segment_pipe.connect(inputnode, "brain_file", seg_at, "brain_file")
    segment_pipe.connect(bin_norm_intensity, 'out_file',
                         seg_at, "brainmask_file")
    segment_pipe.connect(split_seg, 'list_split_files',
                         seg_at, "priors")

    # on segmentation indexed mask (with labels)
    # 1 -> CSF
    # 2 -> GM
    # 3 -> sub cortical?
    # 4 -> WM
    # 5 -> ?

    thd_nodes = {}
    for key, tissue in {0: 'csf', 1: 'gm', 3: 'wm'}.items():

        tmp_node = NodeParams(fsl.Threshold(),
                              params=parse_key(params, "threshold_" + tissue),
                              name="threshold_" + tissue)

        segment_pipe.connect(seg_at, ('segmented_files', get_elem, key),
                             tmp_node, 'in_file')

        thd_nodes[tissue] = tmp_node

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["segmented_file", "threshold_gm", "threshold_wm",
                    "threshold_csf"]),
        name='outputnode')

    segment_pipe.connect(seg_at, 'segmented_file',
                         outputnode, 'segmented_file')
    segment_pipe.connect(thd_nodes["gm"], 'out_file',
                         outputnode, 'threshold_gm')
    segment_pipe.connect(thd_nodes["wm"], 'out_file',
                         outputnode, 'threshold_wm')
    segment_pipe.connect(thd_nodes["csf"], 'out_file',
                         outputnode, 'threshold_csf')

    return segment_pipe


def create_segment_atropos_pipe(params={}, name="segment_atropos_pipe"):
    """
    Description: Segmentation with ANTS atropos script

    Params:
        - Atropos (see :class:`AtroposN4 <macapype.nodes.segment.AtroposN4>`)
        - threshold_gm, threshold_wm, threshold_csf (see `Threshold \
        <https://nipype.readthedocs.io/en/0.12.1/interfaces/generated/nipype.\
        interfaces.fsl.maths.html#threshold>`_ for arguments)

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
    seg_at = NodeParams(AtroposN4(),
                        params=parse_key(params, "Atropos"),
                        name='seg_at')

    segment_pipe.connect(inputnode, "brain_file", seg_at, "brain_file")
    segment_pipe.connect(bin_norm_intensity, 'out_file',
                         seg_at, "brainmask_file")
    segment_pipe.connect(merge_3_elem, 'merged_list',
                         seg_at, "priors")

    # Threshold GM, WM and CSF
    thd_nodes = {}
    for i, tissue in enumerate(['csf', 'gm', 'wm']):
        tmp_node = NodeParams(fsl.Threshold(),
                              params=parse_key(params, "threshold_" + tissue),
                              name="threshold_" + tissue)

        segment_pipe.connect(seg_at, ('segmented_files', get_elem, i),
                             tmp_node, 'in_file')

        thd_nodes[tissue] = tmp_node

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["segmented_file", "threshold_gm", "threshold_wm",
                    "threshold_csf"]),
        name='outputnode')

    segment_pipe.connect(seg_at, 'segmented_file',
                         outputnode, 'segmented_file')
    segment_pipe.connect(thd_nodes["gm"], 'out_file',
                         outputnode, 'threshold_gm')
    segment_pipe.connect(thd_nodes["wm"], 'out_file',
                         outputnode, 'threshold_wm')
    segment_pipe.connect(thd_nodes["csf"], 'out_file',
                         outputnode, 'threshold_csf')

    return segment_pipe

###############################################################################
# old segment, originally from SPM8
###############################################################################


def create_old_segment_pipe(params_template, params={},
                            name="old_segment_pipe"):
    """
    Description: Extract brain using tissues masks output by SPM's old_segment

    Function:

        - Segment the T1 using given priors;
        - Threshold GM, WM and CSF maps;
    Params:

    - segment (see `Segment <https://nipype.readthedocs.io/en/0.12.1/\
    interfaces/generated/nipype.interfaces.spm.preprocess.html#segment>`_)
    - threshold_gm, threshold_wm, threshold_csf (see `Threshold \
    <https://nipype.readthedocs.io/en/0.12.1/interfaces/generated/nipype.\
    interfaces.fsl.maths.html#threshold>`_ for arguments) - also available \
    as :ref:`indiv_params <indiv_params>`
    - dilate_mask (see `DilateMask <https://nipype.readthedocs.io/en/0.12.1/\
    interfaces/generated/nipype.interfaces.fsl.maths.html#dilateimage>`_)
    - erode_mask (see `ErodeMask <https://nipype.readthedocs.io/en/0.12.1/\
    interfaces/generated/nipype.interfaces.fsl.maths.html#erodeimage>`_)


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
    seg_pipe = pe.Workflow(name=name)

    # Creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1', 'indiv_params']),
        name='inputnode'
    )

    assert set_spm(), \
        "Error, SPM was not found, cannot run SPM old segment pipeline"

    unzip = pe.Node(
        interface=niu.Function(input_names=['zipped_file'],
                               output_names=["unzipped_file"],
                               function=gunzip),
        name="unzip")

    seg_pipe.connect(inputnode, 'T1', unzip, 'zipped_file')

    # Segment in to 6 tissues
    segment = NodeParams(spm.Segment(),
                         params=parse_key(params, "segment"),
                         name="old_segment")

    segment.inputs.tissue_prob_maps = [params_template["template_gm"],
                                       params_template["template_wm"],
                                       params_template["template_csf"]]

    seg_pipe.connect(unzip, 'unzipped_file', segment, 'data')

    # Threshold GM, WM and CSF
    thd_nodes = {}
    for tissue in ['gm', 'wm', 'csf']:

        tmp_node = NodeParams(fsl.Threshold(),
                              params=parse_key(params, "threshold_" + tissue),
                              name="threshold_" + tissue)

        seg_pipe.connect(segment, 'native_' + tissue + '_image',
                         tmp_node, 'in_file')

        seg_pipe.connect(
            inputnode, ('indiv_params', parse_key, "threshold_" + tissue),
            tmp_node, "indiv_params")

        thd_nodes[tissue] = tmp_node

    # Creating output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['threshold_gm', 'threshold_wm',
                                      'threshold_csf']),
        name='outputnode')

    seg_pipe.connect(thd_nodes['gm'], 'out_file',
                     outputnode, 'threshold_gm')
    seg_pipe.connect(thd_nodes['wm'], 'out_file',
                     outputnode, 'threshold_wm')
    seg_pipe.connect(thd_nodes['csf'], 'out_file',
                     outputnode, 'threshold_csf')

    return seg_pipe


def create_native_old_segment_pipe(params_template, params={},
                                   name="native_old_segment_pipe"):
    """
    Description: Extract brain using tissues masks output by SPM's old_segment
        function:

        - Segment the T1 using given priors;
        - Threshold GM, WM and CSF maps;
        - Compute union of those 3 tissues with indexes;

    Params:

    - segment (see `Segment <https://nipype.readthedocs.io/en/0.12.1/\
    interfaces/generated/nipype.interfaces.spm.preprocess.html#segment>`_)
    - threshold_gm, threshold_wm, threshold_csf (see `Threshold \
    <https://nipype.readthedocs.io/en/0.12.1/interfaces/generated/nipype.\
    interfaces.fsl.maths.html#threshold>`_ for arguments) - also available \
    as :ref:`indiv_params <indiv_params>`


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
    seg_pipe = pe.Workflow(name=name)

    # Creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1', 'indiv_params', "native_gm",
                                      "native_wm", "native_csf"]),
        name='inputnode'
    )

    assert set_spm(), \
        "Error, SPM was not found, cannot run SPM old segment pipeline"

    unzip = pe.Node(
        interface=niu.Function(input_names=['zipped_file'],
                               output_names=["unzipped_file"],
                               function=gunzip),
        name="unzip")

    seg_pipe.connect(inputnode, 'T1', unzip, 'zipped_file')

    # merging priors as a list
    merge_native_tissues = pe.Node(niu.Function(
        input_names=['elem1', 'elem2', 'elem3'],
        output_names=['merged_list'],
        function=merge_3_elem_to_list), name='merge_native_tissues')

    seg_pipe.connect(inputnode, 'native_gm', merge_native_tissues, "elem1")
    seg_pipe.connect(inputnode, 'native_wm', merge_native_tissues, "elem2")
    seg_pipe.connect(inputnode, 'native_csf', merge_native_tissues, "elem3")

    # Segment in to 6 tissues
    segment = NodeParams(spm.Segment(),
                         params=parse_key(params, "segment"),
                         name="old_segment")

    seg_pipe.connect(merge_native_tissues, 'merged_list',
                     segment, 'tissue_prob_maps')

    seg_pipe.connect(unzip, 'unzipped_file', segment, 'data')

    # Threshold GM, WM and CSF
    thd_nodes = {}
    for tissue in ['gm', 'wm', 'csf']:

        tmp_node = NodeParams(fsl.Threshold(),
                              params=parse_key(params, "threshold_" + tissue),
                              name="threshold_" + tissue)

        seg_pipe.connect(segment, 'native_' + tissue + '_image',
                         tmp_node, 'in_file')

        seg_pipe.connect(
            inputnode, ('indiv_params', parse_key, "threshold_" + tissue),
            tmp_node, "indiv_params")

        thd_nodes[tissue] = tmp_node

    # outputnode
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["threshold_gm", "threshold_wm", "threshold_csf"]),
        name='outputnode')

    seg_pipe.connect(thd_nodes["gm"], 'out_file', outputnode, 'threshold_gm')
    seg_pipe.connect(thd_nodes["wm"], 'out_file', outputnode, 'threshold_wm')
    seg_pipe.connect(thd_nodes["csf"], 'out_file', outputnode, 'threshold_csf')

    return seg_pipe


###############################################################################
# create mask from segment
def create_mask_from_seg_pipe(params={}, name="mask_from_seg_pipe"):

    """
    Description:  mask from segmentation tissues

    #TODO To be added if required (was in old_segment before)

    Function:

        - Compute union of those 3 tissues;
        - Apply morphological opening on the union mask
        - Fill holes

    Inputs:

        mask_gm, mask_wm:
            binary mask for grey matter and white matter
    Outputs:

        fill_holes.out_file:
            filled mask after erode

        fill_holes_dil.out_file
            filled mask after dilate
    """

    # creating pipeline
    seg_pipe = pe.Workflow(name=name)

    # Creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['mask_gm', 'mask_wm', 'mask_csf',
                                      'indiv_params']),
        name='inputnode'
    )

    # bin_gm
    bin_gm = pe.Node(interface=fsl.UnaryMaths(), name="bin_gm")
    bin_gm.inputs.operation = "fillh"

    seg_pipe.connect(inputnode, 'mask_gm',
                                bin_gm, 'in_file')

    # bin_csf
    bin_csf = pe.Node(interface=fsl.UnaryMaths(), name="bin_csf")
    bin_csf.inputs.operation = "fillh"

    seg_pipe.connect(inputnode, 'mask_csf',
                                bin_csf, 'in_file')

    # bin_wm
    bin_wm = pe.Node(interface=fsl.UnaryMaths(), name="bin_wm")
    bin_wm.inputs.operation = "fillh"

    seg_pipe.connect(inputnode, 'mask_wm',
                                bin_wm, 'in_file')

    # Compute union of the 3 tissues
    # Done with 2 fslmaths as it seems to hard to do it
    wmgm_union = pe.Node(fsl.BinaryMaths(), name="wmgm_union")
    wmgm_union.inputs.operation = "add"
    seg_pipe.connect(bin_gm, 'out_file', wmgm_union, 'in_file')
    seg_pipe.connect(bin_wm, 'out_file', wmgm_union, 'operand_file')

    tissues_union = pe.Node(fsl.BinaryMaths(), name="tissues_union")
    tissues_union.inputs.operation = "add"
    seg_pipe.connect(wmgm_union, 'out_file', tissues_union, 'in_file')
    seg_pipe.connect(bin_csf, 'out_file',
                     tissues_union, 'operand_file')

    # Opening (dilating) mask
    dilate_mask = NodeParams(fsl.DilateImage(),
                             params=parse_key(params, "dilate_mask"),
                             name="dilate_mask")

    dilate_mask.inputs.operation = "mean"  # Arbitrary operation
    seg_pipe.connect(tissues_union, 'out_file', dilate_mask, 'in_file')

    # fill holes of dilate_mask
    fill_holes_dil = pe.Node(BinaryFillHoles(), name="fill_holes_dil")
    seg_pipe.connect(dilate_mask, 'out_file', fill_holes_dil, 'in_file')

    # Eroding mask
    erode_mask = NodeParams(fsl.ErodeImage(),
                            params=parse_key(params, "erode_mask"),
                            name="erode_mask")

    seg_pipe.connect(tissues_union, 'out_file', erode_mask, 'in_file')

    # fill holes of erode_mask
    fill_holes = pe.Node(BinaryFillHoles(), name="fill_holes")
    seg_pipe.connect(erode_mask, 'out_file', fill_holes, 'in_file')

    # merge to index
    merge_indexed_mask = NodeParams(
        interface=niu.Function(input_names=["mask_csf_file", "mask_wm_file",
                                            "mask_gm_file", "index_csf",
                                            "index_gm", "index_wm"],
                               output_names=['indexed_mask'],
                               function=merge_masks),
        params=parse_key(params, "merge_indexed_mask"),
        name="merge_indexed_mask")

    seg_pipe.connect(bin_gm, 'out_file', merge_indexed_mask, "mask_gm_file")
    seg_pipe.connect(bin_wm, 'out_file', merge_indexed_mask, "mask_wm_file")
    seg_pipe.connect(bin_csf, 'out_file',
                     merge_indexed_mask, "mask_csf_file")

    return seg_pipe
