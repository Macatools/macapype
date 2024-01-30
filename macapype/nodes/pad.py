

import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from macapype.nodes.prepare import padding_cropped_img

from nipype.interfaces.niftyreg.regutils import RegResample


def pad_back(seg_pipe, data_preparation_pipe, inputnode,
             node, nodefile,
             outputnode, outputnodefile,
             params):

    pad_nodename = "pad_" + outputnodefile

    if "short_preparation_pipe" in params.keys():
        if "crop_T1" in params["short_preparation_pipe"].keys():

            print("Padding mask in native space")
            pad_node = pe.Node(
                niu.Function(
                    input_names=[
                        'cropped_img_file',
                        'orig_img_file',
                        'indiv_crop'],
                    output_names=['padded_img_file'],
                    function=padding_cropped_img),
                name=pad_nodename)

            seg_pipe.connect(
                node, nodefile,
                pad_node, "cropped_img_file")

            seg_pipe.connect(
                data_preparation_pipe, "outputnode.native_T1",
                pad_node, "orig_img_file")

            seg_pipe.connect(
                inputnode, "indiv_params",
                pad_node, "indiv_crop")

            seg_pipe.connect(
                pad_node, "padded_img_file",
                outputnode, outputnodefile)

        else:
            print("Using reg_aladin transfo to pad mask back")
            pad_node = pe.Node(
                RegResample(inter_val="NN"),
                name=pad_nodename)

            seg_pipe.connect(
                node, nodefile,
                pad_node, "flo_file")

            seg_pipe.connect(
                data_preparation_pipe, "outputnode.native_T1",
                pad_node, "ref_file")

            seg_pipe.connect(
                data_preparation_pipe, "inv_tranfo.out_file",
                pad_node, "trans_file")

            # outputnode
            seg_pipe.connect(
                pad_node, "out_file",
                outputnode, outputnodefile)

    elif "long_single_preparation_pipe" in params.keys():
        if "prep_T1" in params["long_single_preparation_pipe"].keys():

            print("Padding mask in native space")
            pad_node = pe.Node(
                niu.Function(
                    input_names=[
                        'cropped_img_file',
                        'orig_img_file',
                        'indiv_crop'],
                    output_names=['padded_img_file'],
                    function=padding_cropped_img),
                name=pad_nodename)

            seg_pipe.connect(
                node, nodefile,
                pad_node, "cropped_img_file")

            seg_pipe.connect(
                data_preparation_pipe, "outputnode.native_T1",
                pad_node, "orig_img_file")

            seg_pipe.connect(
                inputnode, "indiv_params",
                pad_node, "indiv_crop")

            seg_pipe.connect(
                pad_node, "padded_img_file",
                outputnode, outputnodefile)

    return pad_node


def apply_to_stereo(seg_pipe, native_to_stereo_pipe,
                    pad_node, pad_nodefile,
                    outputnode, outputnodefile):

    apply_nodename = "apply_" + outputnodefile

    # apply stereo to masked_debiased_T1
    apply_node = pe.Node(
        RegResample(pad_val=0.0),
        name=apply_nodename)

    seg_pipe.connect(
        pad_node, pad_nodefile,
        apply_node, "flo_file")

    seg_pipe.connect(
        native_to_stereo_pipe,
        'outputnode.native_to_stereo_trans',
        apply_node, "trans_file")

    seg_pipe.connect(
        native_to_stereo_pipe,
        'outputnode.stereo_native_T1',
        apply_node, "ref_file")

    # output
    seg_pipe.connect(
        apply_node, "out_file",
        outputnode, outputnodefile)

    return apply_node
