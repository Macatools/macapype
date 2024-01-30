import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl

import nipype.interfaces.spm as spm

from ..nodes.segment import (AtroposN4, merge_masks,
                             merge_imgs, split_indexed_mask, copy_header,
                             compute_5tt, fill_list_vol)


from macapype.nodes.surface import wrap_afni_IsoSurface

from ..utils.misc import (gunzip, merge_3_elem_to_list,
                          get_pattern, get_list_length, get_index)

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

    if "use_priors" in params.keys():

        # merging priors as a list
        split_seg = pe.Node(niu.Function(
            input_names=['nii_file'],
            output_names=['list_split_files'],
            function=split_indexed_mask), name='split_seg')

        # segment_pipe.connect(copy_header_to_seg, 'modified_img',
        segment_pipe.connect(inputnode, "seg_file",
                             split_seg, "nii_file")

    # Atropos
    seg_at = NodeParams(AtroposN4(),
                        params=parse_key(params, "Atropos"),
                        name='seg_at')

    segment_pipe.connect(inputnode, "brain_file",
                         seg_at, "brain_file")

    segment_pipe.connect(bin_norm_intensity, 'out_file',
                         seg_at, "brainmask_file")

    if "use_priors" in params.keys():

        seg_at.inputs.prior_weight = params["use_priors"]

        segment_pipe.connect(split_seg, 'list_split_files',
                             seg_at, "priors")

        segment_pipe.connect(split_seg, ('list_split_files', get_list_length),
                             seg_at, "numberOfClasses")

    # split dseg_mask
    split_dseg_mask = pe.Node(
        interface=niu.Function(input_names=["nii_file"],
                               output_names=["list_split_files"],
                               function=split_indexed_mask),
        name="split_dseg_mask")

    segment_pipe.connect(seg_at, 'segmented_file',
                         split_dseg_mask, "nii_file")

    # on segmentation indexed mask (with labels)
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["segmented_file", "threshold_gm", "threshold_wm",
                    "threshold_csf", "prob_gm", "prob_wm",
                    "prob_csf"]),
        name='outputnode')

    segment_pipe.connect(seg_at, 'segmented_file',
                         outputnode, 'segmented_file')

    if "tissue_dict" in params.keys():
        tissue_dict = params["tissue_dict"]

    else:
        # NMT_v2.0 (5 tissus)
        # tissue_dict = {'csf': [1, 5], 'gm': [2, 3],  'wm': 4}

        # MBM 3.0.1 three tissue
        tissue_dict = {'csf': 3, 'gm': 1,  'wm': 2}

    print("Using tissue dict {}".format(tissue_dict))

    # merging dseg
    for tissue, index_tissue in tissue_dict.items():
        if isinstance(index_tissue, list):

            # Merging as file list
            merge_dseg_list = pe.Node(niu.Merge(len(index_tissue)),
                                      name="merge_dseg_list_" + tissue)

            for index, sub_index_tissue in enumerate(index_tissue):
                segment_pipe.connect(
                    split_dseg_mask,
                    ('list_split_files', get_index, sub_index_tissue),
                    merge_dseg_list, 'in' + str(index+1))

            # Merging files in the same nifti
            merge_dseg_tissues = pe.Node(
                niu.Function(
                    input_names=["list_img_files"],
                    output_names=["merged_img_file"],
                    function=merge_imgs),
                name="merge_dseg_tissues_" + tissue)

            segment_pipe.connect(merge_dseg_list, "out",
                                 merge_dseg_tissues, 'list_img_files')

            # thr output
            segment_pipe.connect(merge_dseg_tissues, 'merged_img_file',
                                 outputnode, 'threshold_'+tissue)

        else:

            # thresh output
            segment_pipe.connect(
                split_dseg_mask, ('list_split_files', get_index,
                                  index_tissue),
                outputnode, 'threshold_'+tissue)

    # merging probseg
    for tissue, index_tissue in tissue_dict.items():
        if isinstance(index_tissue, list):

            # Merging as file list
            merge_list = pe.Node(niu.Merge(len(index_tissue)),
                                 name="merge_list_" + tissue)

            for index, sub_index_tissue in enumerate(index_tissue):
                segment_pipe.connect(
                    seg_at,
                    ('segmented_files', get_pattern,
                     "SegmentationPosteriors{:02d}".format(
                         int(sub_index_tissue))),
                    merge_list, 'in' + str(index+1))

            # Merging files in the same nifti
            merge_tissues = pe.Node(
                niu.Function(
                    input_names=["list_img_files"],
                    output_names=["merged_img_file"],
                    function=merge_imgs),
                name="merge_tissues_" + tissue)

            segment_pipe.connect(merge_list, "out",
                                 merge_tissues, 'list_img_files')

            # prob output
            segment_pipe.connect(merge_tissues, 'merged_img_file',
                                 outputnode, 'prob_'+tissue)

        else:

            # prob output
            segment_pipe.connect(
                seg_at,
                ('segmented_files', get_pattern,
                 "SegmentationPosteriors{:02d}".format(int(index_tissue))),
                outputnode, 'prob_'+tissue)

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

    if "use_priors" in params.keys():

        reorient_csf = pe.Node(fsl.utils.Reorient2Std(), name="reorient_csf")

        segment_pipe.connect(inputnode, 'csf_prior_file',
                             reorient_csf, "in_file")

        reorient_gm = pe.Node(fsl.utils.Reorient2Std(), name="reorient_gm")

        segment_pipe.connect(inputnode, 'gm_prior_file',
                             reorient_gm, "in_file")

        reorient_wm = pe.Node(fsl.utils.Reorient2Std(), name="reorient_wm")

        segment_pipe.connect(inputnode, 'wm_prior_file',
                             reorient_wm, "in_file")

        # copying header from img to csf_prior_file
        copy_header_to_csf = pe.Node(niu.Function(
            input_names=['ref_img', 'img_to_modify'],
            output_names=['modified_img'],
            function=copy_header), name='copy_header_to_csf')

        segment_pipe.connect(inputnode, "brain_file",
                             copy_header_to_csf, "ref_img")
        segment_pipe.connect(reorient_csf, 'out_file',
                             copy_header_to_csf, "img_to_modify")

        # copying header from img to gm_prior_file
        copy_header_to_gm = pe.Node(niu.Function(
            input_names=['ref_img', 'img_to_modify'],
            output_names=['modified_img'],
            function=copy_header), name='copy_header_to_gm')

        segment_pipe.connect(inputnode, "brain_file",
                             copy_header_to_gm, "ref_img")
        segment_pipe.connect(reorient_gm, 'out_file',
                             copy_header_to_gm, "img_to_modify")

        # copying header from img to wm_prior_file
        copy_header_to_wm = pe.Node(niu.Function(
            input_names=['ref_img', 'img_to_modify'],
            output_names=['modified_img'],
            function=copy_header), name='copy_header_to_wm')

        segment_pipe.connect(inputnode, "brain_file",
                             copy_header_to_wm, "ref_img")
        segment_pipe.connect(reorient_wm, 'out_file',
                             copy_header_to_wm, "img_to_modify")

        # merging priors as a list
        merge_3_elem = pe.Node(niu.Function(
            input_names=['elem1', 'elem2', 'elem3'],
            output_names=['merged_list'],
            function=merge_3_elem_to_list), name='merge_3_elem')

        # was like this before (1 -> csf, 2 -> gm, 3 -> wm, to check)
        segment_pipe.connect(copy_header_to_csf, 'modified_img',
                             merge_3_elem, "elem1")
        segment_pipe.connect(copy_header_to_gm, 'modified_img',
                             merge_3_elem, "elem2")
        segment_pipe.connect(copy_header_to_wm, 'modified_img',
                             merge_3_elem, "elem3")

    # Atropos
    seg_at = NodeParams(AtroposN4(),
                        params=parse_key(params, "Atropos"),
                        name='seg_at')

    segment_pipe.connect(inputnode, "brain_file", seg_at, "brain_file")
    segment_pipe.connect(bin_norm_intensity, 'out_file',
                         seg_at, "brainmask_file")

    if "use_priors" in params.keys():
        if "Atropos" in params.keys():
            if "numberOfClasses" in params["Atropos"].keys():
                nb_classes = params["Atropos"]["numberOfClasses"]

                fill_nb_classes = pe.Node(
                    interface=niu.Function(
                        input_names=['list_vol', "nb_classes"],
                        output_names=["filled_list_vol"],
                        function=fill_list_vol),
                    name="fill_nb_classes")

                segment_pipe.connect(merge_3_elem, 'merged_list',
                                     fill_nb_classes, "list_vol")

                fill_nb_classes.inputs.nb_classes = nb_classes

                segment_pipe.connect(fill_nb_classes, 'filled_list_vol',
                                     seg_at, "priors")

            else:
                print("No numberOfClasses was specified, adding default (3)")
                seg_at.inputs.numberOfClasses = 3

                segment_pipe.connect(merge_3_elem, 'merged_list',
                                     seg_at, "priors")

        else:
            segment_pipe.connect(merge_3_elem, 'merged_list',
                                 seg_at, "priors")

        seg_at.inputs.prior_weight = params["use_priors"]

    # split dseg_mask
    split_dseg_mask = pe.Node(
        interface=niu.Function(input_names=["nii_file"],
                               output_names=["list_split_files"],
                               function=split_indexed_mask),
        name="split_dseg_mask")

    segment_pipe.connect(seg_at, 'segmented_file',
                         split_dseg_mask, "nii_file")

    # on segmentation indexed mask (with labels)
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["segmented_file", "threshold_gm", "threshold_wm",
                    "threshold_csf", "prob_gm", "prob_wm",
                    "prob_csf"]),
        name='outputnode')

    segment_pipe.connect(seg_at, 'segmented_file',
                         outputnode, 'segmented_file')

    if "tissue_dict" in params.keys():
        tissue_dict = params["tissue_dict"]

    else:
        # NMT_v2.0 (5 tissus)
        # tissue_dict = {'csf': [1, 5], 'gm': [2, 3],  'wm': 4}

        # MBM 3.0.1 three tissue
        tissue_dict = {'csf': 3, 'gm': 1,  'wm': 2}

    print("Using tissue dict {}".format(tissue_dict))

    # merging dseg
    for tissue, index_tissue in tissue_dict.items():
        if isinstance(index_tissue, list):

            # Merging as file list
            merge_dseg_list = pe.Node(niu.Merge(len(index_tissue)),
                                      name="merge_dseg_list_" + tissue)

            for index, sub_index_tissue in enumerate(index_tissue):
                segment_pipe.connect(
                    split_dseg_mask,
                    ('list_split_files', get_index, sub_index_tissue),
                    merge_dseg_list, 'in' + str(index+1))

            # Merging files in the same nifti
            merge_dseg_tissues = pe.Node(
                niu.Function(
                    input_names=["list_img_files"],
                    output_names=["merged_img_file"],
                    function=merge_imgs),
                name="merge_dseg_tissues_" + tissue)

            segment_pipe.connect(merge_dseg_list, "out",
                                 merge_dseg_tissues, 'list_img_files')

            # thr output
            segment_pipe.connect(merge_dseg_tissues, 'merged_img_file',
                                 outputnode, 'threshold_'+tissue)

        else:

            # thresh output
            segment_pipe.connect(
                split_dseg_mask, ('list_split_files', get_index,
                                  index_tissue),
                outputnode, 'threshold_'+tissue)

    # merging probseg
    for tissue, index_tissue in tissue_dict.items():
        if isinstance(index_tissue, list):

            # Merging as file list
            merge_list = pe.Node(niu.Merge(len(index_tissue)),
                                 name="merge_list_" + tissue)

            for index, sub_index_tissue in enumerate(index_tissue):
                segment_pipe.connect(
                    seg_at,
                    ('segmented_files', get_pattern,
                     "SegmentationPosteriors{:02d}".format(
                         int(sub_index_tissue))),
                    merge_list, 'in' + str(index+1))

            # Merging files in the same nifti
            merge_tissues = pe.Node(
                niu.Function(
                    input_names=["list_img_files"],
                    output_names=["merged_img_file"],
                    function=merge_imgs),
                name="merge_tissues_" + tissue)

            segment_pipe.connect(merge_list, "out",
                                 merge_tissues, 'list_img_files')

            # prob output
            segment_pipe.connect(merge_tissues, 'merged_img_file',
                                 outputnode, 'prob_'+tissue)

        else:

            if "use_priors" in params.keys():

                # prob output
                segment_pipe.connect(
                    seg_at,
                    ('segmented_files', get_pattern,
                     "SegmentationPosteriors{:02d}".format(int(index_tissue))),
                    outputnode, 'prob_'+tissue)
            else:

                # prob output
                segment_pipe.connect(
                    seg_at,
                    ('segmented_files', get_pattern,
                     "SegmentationPosteriors{}".format(int(index_tissue))),
                    outputnode, 'prob_'+tissue)

    return segment_pipe


def create_5tt_pipe(params={}, name="export_5tt_pipe"):

    # creating pipeline
    export_5tt_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=["gm_file", "wm_file", "csf_file"]),
        name='inputnode')

    # bin_gm
    bin_gm = pe.Node(interface=fsl.UnaryMaths(), name="bin_gm")
    bin_gm.inputs.operation = "bin"

    export_5tt_pipe.connect(inputnode, 'gm_file',
                            bin_gm, 'in_file')

    # bin_csf
    bin_csf = pe.Node(interface=fsl.UnaryMaths(), name="bin_csf")
    bin_csf.inputs.operation = "bin"

    export_5tt_pipe.connect(inputnode, 'csf_file',
                            bin_csf, 'in_file')

    # bin_wm
    bin_wm = pe.Node(interface=fsl.UnaryMaths(), name="bin_wm")
    bin_wm.inputs.operation = "bin"

    export_5tt_pipe.connect(inputnode, 'wm_file',
                            bin_wm, 'in_file')

    # export_5tt
    export_5tt = pe.Node(
        niu.Function(input_names=["gm_file", "wm_file", "csf_file"],
                     output_names=["gen_5tt_file"],
                     function=compute_5tt),
        name="export_5tt")

    export_5tt_pipe.connect(bin_gm, 'out_file', export_5tt, 'gm_file')
    export_5tt_pipe.connect(bin_wm, 'out_file', export_5tt, 'wm_file')
    export_5tt_pipe.connect(bin_csf, 'out_file', export_5tt, 'csf_file')

    return export_5tt_pipe


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
                                      'threshold_csf', 'prob_gm', 'prob_wm',
                                      'prob_csf']),
        name='outputnode')

    seg_pipe.connect(thd_nodes['gm'], 'out_file',
                     outputnode, 'threshold_gm')
    seg_pipe.connect(thd_nodes['wm'], 'out_file',
                     outputnode, 'threshold_wm')
    seg_pipe.connect(thd_nodes['csf'], 'out_file',
                     outputnode, 'threshold_csf')

    seg_pipe.connect(segment, 'native_gm_image',
                     outputnode, 'prob_gm')
    seg_pipe.connect(segment, 'native_wm_image',
                     outputnode, 'prob_wm')
    seg_pipe.connect(segment, 'native_csf_image',
                     outputnode, 'prob_csf')

    return seg_pipe


def create_native_old_segment_seg_pipe(params_template, params={},
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
        niu.IdentityInterface(
            fields=['indiv_params', "native_T1", "inv_transfo_file"]),
        name='inputnode'
    )

    assert set_spm(), \
        "Error, SPM was not found, cannot run SPM old segment pipeline"

    # unzip T1
    unzip = pe.Node(
        interface=niu.Function(input_names=['zipped_file'],
                               output_names=["unzipped_file"],
                               function=gunzip),
        name="unzip")

    seg_pipe.connect(inputnode, 'native_T1', unzip, 'zipped_file')

    # merging priors as a list
    split_seg = pe.Node(niu.Function(
        input_names=['nii_file'],
        output_names=['list_split_files'],
        function=split_indexed_mask), name='split_seg')

    split_seg.inputs.nii_file = params_template["template_seg"]

    # tissue_to_nat
    register_tissue_to_nat = pe.MapNode(
        fsl.ApplyXFM(),
        iterfield=["in_file"],
        name="register_tissue_to_nat")

    register_tissue_to_nat.inputs.output_type = "NIFTI"  # for SPM segment
    register_tissue_to_nat.inputs.interp = "nearestneighbour"

    seg_pipe.connect(split_seg, 'list_split_files',
                     register_tissue_to_nat, 'in_file')

    # joining (Merge)

    # Segment in to 6 tissues
    segment = NodeParams(spm.Segment(),
                         params=parse_key(params, "segment"),
                         name="old_segment")

    seg_pipe.connect(unzip, 'unzipped_file', segment, 'data')

    segment = pe.JoinNode(interface=spm.Segment(),
                          joinsource="register_tissue_to_nat",
                          joinfield="tissue_prob_maps",
                          name="old_segment")

    seg_pipe.connect(register_tissue_to_nat, "out_file",
                     segment, "tissue_prob_maps")

    seg_pipe.connect(unzip, 'unzipped_file', segment, 'data')

    # outputnode
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["threshold_gm", "threshold_wm", "threshold_csf",
                    "prob_gm", "prob_wm", "prob_csf"]),
        name='outputnode')

    seg_pipe.connect(segment, 'native_gm_image', outputnode, 'prob_gm')
    seg_pipe.connect(segment, 'native_wm_image', outputnode, 'prob_wm')
    seg_pipe.connect(segment, 'native_csf_image', outputnode, 'prob_csf')

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
        niu.IdentityInterface(
            fields=['indiv_params', "native_T1", "inv_transfo_file"]),
        name='inputnode'
    )

    assert set_spm(), \
        "Error, SPM was not found, cannot run SPM old segment pipeline"

    # gm
    register_gm_to_nat = pe.Node(fsl.ApplyXFM(), name="register_gm_to_nat")
    register_gm_to_nat.inputs.output_type = "NIFTI"  # for SPM segment
    register_gm_to_nat.inputs.interp = "nearestneighbour"

    register_gm_to_nat.inputs.in_file = params_template["template_gm"]

    seg_pipe.connect(inputnode, 'native_T1',
                     register_gm_to_nat, 'reference')

    seg_pipe.connect(inputnode, 'inv_transfo_file',
                     register_gm_to_nat, "in_matrix_file")

    # wm
    register_wm_to_nat = pe.Node(fsl.ApplyXFM(), name="register_wm_to_nat")
    register_wm_to_nat.inputs.output_type = "NIFTI"  # for SPM segment
    register_wm_to_nat.inputs.interp = "nearestneighbour"

    register_wm_to_nat.inputs.in_file = params_template["template_wm"]

    seg_pipe.connect(inputnode, 'native_T1',
                     register_wm_to_nat, 'reference')

    seg_pipe.connect(inputnode, 'inv_transfo_file',
                     register_wm_to_nat, "in_matrix_file")

    # csf
    register_csf_to_nat = pe.Node(fsl.ApplyXFM(), name="register_csf_to_nat")
    register_csf_to_nat.inputs.output_type = "NIFTI"  # for SPM segment
    register_csf_to_nat.inputs.interp = "nearestneighbour"

    register_csf_to_nat.inputs.in_file = params_template["template_csf"]

    seg_pipe.connect(inputnode, 'native_T1',
                     register_csf_to_nat, 'reference')

    seg_pipe.connect(inputnode, 'inv_transfo_file',
                     register_csf_to_nat, "in_matrix_file")
    # unzip T1
    unzip = pe.Node(
        interface=niu.Function(input_names=['zipped_file'],
                               output_names=["unzipped_file"],
                               function=gunzip),
        name="unzip")

    seg_pipe.connect(inputnode, 'native_T1', unzip, 'zipped_file')

    # merge_tissue_files
    merge_tissue_files = pe.Node(
        interface=niu.Merge(3),
        name="merge_tissue_files")

    seg_pipe.connect(register_gm_to_nat, "out_file", merge_tissue_files, 'in1')
    seg_pipe.connect(register_wm_to_nat, "out_file", merge_tissue_files, 'in2')
    seg_pipe.connect(register_csf_to_nat, "out_file",
                     merge_tissue_files, 'in3')

    # Segment in to 6 tissues
    segment = NodeParams(spm.Segment(),
                         params=parse_key(params, "segment"),
                         name="old_segment")

    seg_pipe.connect(merge_tissue_files, "out",
                     segment, "tissue_prob_maps")

    seg_pipe.connect(unzip, 'unzipped_file', segment, 'data')

    # threshold_gm
    threshold_gm = NodeParams(fsl.Threshold(),
                              params=parse_key(params, "threshold_gm"),
                              name="threshold_gm")

    seg_pipe.connect(segment, 'native_gm_image', threshold_gm, 'in_file')

    seg_pipe.connect(
        inputnode, ('indiv_params', parse_key, "threshold_gm"),
        threshold_gm, "indiv_params")

    # threshold_wm
    threshold_wm = NodeParams(fsl.Threshold(),
                              params=parse_key(params, "threshold_wm"),
                              name="threshold_wm")

    seg_pipe.connect(segment, 'native_wm_image', threshold_wm, 'in_file')

    seg_pipe.connect(
        inputnode, ('indiv_params', parse_key, "threshold_wm"),
        threshold_wm, "indiv_params")

    # threshold_csf
    threshold_csf = NodeParams(fsl.Threshold(),
                               params=parse_key(params, "threshold_csf"),
                               name="threshold_csf")

    seg_pipe.connect(segment, 'native_csf_image', threshold_csf, 'in_file')

    seg_pipe.connect(
        inputnode, ('indiv_params', parse_key, "threshold_csf"),
        threshold_csf, "indiv_params")

    # outputnode
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["threshold_gm", "threshold_wm", "threshold_csf",
                    "prob_gm", "prob_wm", "prob_csf"]),
        name='outputnode')

    seg_pipe.connect(threshold_gm, 'out_file', outputnode, 'threshold_gm')
    seg_pipe.connect(threshold_wm, 'out_file', outputnode, 'threshold_wm')
    seg_pipe.connect(threshold_csf, 'out_file', outputnode, 'threshold_csf')

    seg_pipe.connect(segment, 'native_gm_image', outputnode, 'prob_gm')
    seg_pipe.connect(segment, 'native_wm_image', outputnode, 'prob_wm')
    seg_pipe.connect(segment, 'native_csf_image', outputnode, 'prob_csf')

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

    # Compute union of the 3 tissues
    # Done with 2 fslmaths as it seems to hard to do it
    wmgm_union = pe.Node(fsl.BinaryMaths(), name="wmgm_union")
    wmgm_union.inputs.operation = "add"
    seg_pipe.connect(bin_gm, 'out_file', wmgm_union, 'in_file')
    seg_pipe.connect(bin_wm, 'out_file', wmgm_union, 'operand_file')

    # bin mask
    bin_mask = pe.Node(interface=fsl.UnaryMaths(), name="bin_mask")
    bin_mask.inputs.operation = "bin"

    seg_pipe.connect(wmgm_union, 'out_file', bin_mask, 'in_file')

    # wmgm2mesh
    wmgm2mesh = pe.Node(
        interface=niu.Function(input_names=["nii_file"],
                               output_names=["stl_file"],
                               function=wrap_afni_IsoSurface),
        name="wmgm2mesh")

    seg_pipe.connect(bin_mask, 'out_file', wmgm2mesh, "nii_file")

    return seg_pipe
