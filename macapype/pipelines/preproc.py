
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
# from nipype.interfaces.freesurfer.preprocess import MRIConvert

from ..nodes.preproc import average_align, FslOrient

from ..nodes.extract_brain import T1xT2BET


def create_reorient_pipeline(name="reorient_pipe",
                             new_dims=("x", "z", "-y")):

    """
    By kepkee:
    fslswapdim image_bad x z -y image_good
    fslorient -deleteorient image_good.nii.gz;
    fslorient -setqformcode 1 image_good.nii.gz
    """

    # creating pipeline
    reorient_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['image']),
        name='inputnode'
    )

    swap_dim = pe.Node(fsl.SwapDimensions(new_dims=new_dims),
                       name="swap_dim")
    reorient_pipe.connect(inputnode, 'image', swap_dim, 'in_file')

    deorient = pe.Node(FslOrient(main_option="deleteorient"),
                       name="deorient")
    reorient_pipe.connect(swap_dim, 'out_file', deorient, 'in_file')

    reorient = pe.Node(FslOrient(main_option="setqformcode", code=1),
                       name="reorient")
    reorient_pipe.connect(deorient, 'out_file', reorient, 'in_file')

    return reorient_pipe


def create_preproc_pipe(params, name="preproc_pipe"):
    """
    preprocessing:
    - av = checking if multiples T1 and T2 and if it is the case,
    coregister and average (~ flirt_average)
    - coregister T2 on T1 with FLIRT
    - crop using .cropbox file
    """

    # creating pipeline
    preproc_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1', 'T2']),
        name='inputnode'
    )

    # avererge if multiple T1
    av_T1 = pe.Node(
        niu.Function(input_names=['list_img'],
                     output_names=['avg_img'],
                     function=average_align),
        name="av_T1")

    preproc_pipe.connect(inputnode, 'T1', av_T1, 'list_img')

    # avererge if multiple T2
    av_T2 = pe.Node(niu.Function(
        input_names=['list_img'],
        output_names=['avg_img'],
        function=average_align), name="av_T2")

    preproc_pipe.connect(inputnode, 'T2', av_T2, 'list_img')

    if "reorient" in params.keys():

        if "new_dims" in params["reorient"].keys():
            new_dims = tuple(params["reorient"]["new_dims"].split())

        else:
            new_dims = ("x", "z", "-y")

        reorient_T1_pipe = create_reorient_pipeline(name="reorient_T1_pipe",
                                                    new_dims=new_dims)
        preproc_pipe.connect(av_T1, 'avg_img',
                             reorient_T1_pipe, 'inputnode.image')

        reorient_T2_pipe = create_reorient_pipeline(name="reorient_T2_pipe",
                                                    new_dims=new_dims)
        preproc_pipe.connect(av_T2, 'avg_img',
                             reorient_T2_pipe, 'inputnode.image')

    if "bet_crop" in params.keys():

        print('bet_crop is in params')

        # Brain extraction (unused) + Cropping
        bet_crop = pe.Node(T1xT2BET(), name='bet_crop')

        if "m" in params["bet_crop"].keys():
            bet_crop.inputs.m = params["bet_crop"]["m"]

        if "aT2" in params["bet_crop"].keys():
            bet_crop.inputs.aT2 = params["bet_crop"]["aT2"]

        if "c" in params["bet_crop"].keys():
            bet_crop.inputs.c = params["bet_crop"]["c"]

        if "n" in params["bet_crop"].keys():
            bet_crop.inputs.n = params["bet_crop"]["n"]

        if "f" in params["bet_crop"].keys():
            bet_crop.inputs.f = params["bet_crop"]["f"]

        if "g" in params["bet_crop"].keys():
            bet_crop.inputs.g = params["bet_crop"]["g"]

        if "reorient" in params.keys():

            preproc_pipe.connect(reorient_T1_pipe, 'swap_dim.out_file',
                                 bet_crop, 't1_file')
            preproc_pipe.connect(reorient_T2_pipe, 'swap_dim.out_file',
                                 bet_crop, 't2_file')
        else:
            preproc_pipe.connect(av_T1, 'avg_img', bet_crop, 't1_file')
            preproc_pipe.connect(av_T2, 'avg_img', bet_crop, 't2_file')

    elif "crop" in params.keys():
        print('crop is in params')

        assert "croplist" in params["crop"].keys(), \
            "Error, croplist is not specified for crop node, breaking"

        # align avg T2 on avg T1
        align_T2_on_T1 = pe.Node(fsl.FLIRT(), name="align_T2_on_T1")
        align_T2_on_T1.inputs.dof = 6

        # cropping
        # Crop bounding box for T1
        crop_bb_T1 = pe.Node(fsl.ExtractROI(), name='crop_bb_T1')
        crop_bb_T1.inputs.args = params["crop"]["croplist"]

        # Crop bounding box for T2
        crop_bb_T2 = pe.Node(fsl.ExtractROI(), name='crop_bb_T2')
        crop_bb_T2.inputs.args = params["crop"]["croplist"]

        if "reorient" in params.keys():
            preproc_pipe.connect(reorient_T1_pipe, 'swap_dim.out_file',
                                 align_T2_on_T1, 'reference')
            preproc_pipe.connect(reorient_T2_pipe, 'swap_dim.out_file',
                                 align_T2_on_T1, 'in_file')

            preproc_pipe.connect(reorient_T1_pipe, 'swap_dim.out_file',
                                 crop_bb_T1, 'in_file')
        else:
            preproc_pipe.connect(av_T1, 'avg_img', align_T2_on_T1, 'reference')
            preproc_pipe.connect(av_T2, 'avg_img', align_T2_on_T1, 'in_file')

            preproc_pipe.connect(av_T1, 'avg_img', crop_bb_T1, 'in_file')

        preproc_pipe.connect(align_T2_on_T1, "out_file", crop_bb_T2, 'in_file')

    return preproc_pipe


###############################################################################
# Old version of align_crop

# on the fly
def read_cropbox(cropbox_file):

    import os.path as op

    assert op.exists(cropbox_file), \
        "Error {} do not exists".format(cropbox_file)

    with open(cropbox_file) as f:
        crop_list = []
        for line in f.readlines():
            print(line.strip().split())
            crop_list.append(tuple(map(int, map(float, line.strip().split()))))

    return crop_list


def create_average_align_crop_pipe(name='average_align_pipe'):
    """
    preprocessing:
    - av = checking if multiples T1 and T2 and if it is the case,
    coregister and average (~ flirt_average)
    - coregister T2 on T1 with FLIRT
    - crop using .cropbox file
    """

    # creating pipeline
    preproc_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1', 'T2', 'T1cropbox', 'T2cropbox']),
        name='inputnode')

    av_T1 = pe.Node(niu.Function(input_names=['list_img'],
                                 output_names=['avg_img'],
                                 function=average_align), name="av_T1")

    preproc_pipe.connect(inputnode, 'T1', av_T1, 'list_img')

    av_T2 = pe.Node(niu.Function(input_names=['list_img'],
                                 output_names=['avg_img'],
                                 function=average_align), name="av_T2")

    preproc_pipe.connect(inputnode, 'T2', av_T2, 'list_img')

    # align avg T2 on avg T1
    align_T2_on_T1 = pe.Node(fsl.FLIRT(), name="align_T2_on_T1")
    preproc_pipe.connect(av_T1, 'avg_img', align_T2_on_T1, 'reference')
    preproc_pipe.connect(av_T2, 'avg_img', align_T2_on_T1, 'in_file')
    align_T2_on_T1.inputs.dof = 6

    # cropping
    # Crop bounding box for T1
    crop_bb_T1 = pe.Node(fsl.ExtractROI(), name='crop_bb_T1')

    preproc_pipe.connect(inputnode, ("T1cropbox", read_cropbox),
                         crop_bb_T1, 'crop_list')

    preproc_pipe.connect(av_T1, "avg_img", crop_bb_T1, 'in_file')

    # Crop bounding box for T2
    crop_bb_T2 = pe.Node(fsl.ExtractROI(), name='crop_bb_T2')

    preproc_pipe.connect(inputnode, ("T2cropbox", read_cropbox),
                         crop_bb_T2, 'crop_list')

    preproc_pipe.connect(align_T2_on_T1, "out_file", crop_bb_T2, 'in_file')

    return preproc_pipe


def create_average_align_pipe(name='average_align_pipe'):
    """
    preprocessing:
    - av = checking if multiples T1 and T2 and if it is the case,
    coregister and average (~ flirt_average)
    - coregister T2 on T1 with FLIRT
    """

    # creating pipeline
    preproc_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1', 'T2']),
        name='inputnode')

    av_T1 = pe.Node(
        niu.Function(input_names=['list_img'],
                     output_names=['avg_img'],
                     function=average_align),
        name="av_T1")

    preproc_pipe.connect(inputnode, 'T1', av_T1, 'list_img')

    av_T2 = pe.Node(niu.Function(
        input_names=['list_img'],
        output_names=['avg_img'],
        function=average_align), name="av_T2")

    preproc_pipe.connect(inputnode, 'T2', av_T2, 'list_img')

    # align avg T2 on avg T1
    align_T2_on_T1 = pe.Node(fsl.FLIRT(), name="align_T2_on_T1")
    preproc_pipe.connect(av_T1, 'avg_img', align_T2_on_T1, 'reference')
    preproc_pipe.connect(av_T2, 'avg_img', align_T2_on_T1, 'in_file')
    align_T2_on_T1.inputs.dof = 6

    return preproc_pipe
