

import nipype.pipeline.engine as pe

from nipype.interfaces.niftyreg.regutils import RegResample


def pad_back(seg_pipe, data_preparation_pipe, inputnode,
             node, nodefile,
             outputnode, outputnodefile,
             params):

    pad_nodename = "pad_" + outputnodefile

    if "short_preparation_pipe" in params.keys():

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
