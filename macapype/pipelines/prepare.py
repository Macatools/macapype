
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.ants as ants

from nipype.interfaces.ants.segmentation import DenoiseImage

from ..utils.utils_nodes import NodeParams, MapNodeParams
from ..utils.misc import parse_key

from ..nodes.prepare import average_align, FslOrient
from ..nodes.extract_brain import T1xT2BET


def _create_reorient_pipeline(name="reorient_pipe",
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


def create_data_preparation_pipe(params, name="data_preparation_pipe"):
    """
    prepare:
    - av = checking if multiples T1 and T2 and if it is the case,
    coregister and average (~ flirt_average)
    - coregister T2 on T1 with FLIRT
    - crop using .cropbox file
    """

    # creating pipeline
    data_preparation_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1', 'T2', 'indiv_params']),
        name='inputnode'
    )

    # avererge if multiple T1
    av_T1 = pe.Node(
        niu.Function(input_names=['list_img'],
                     output_names=['avg_img'],
                     function=average_align),
        name="av_T1")

    data_preparation_pipe.connect(inputnode, 'T1', av_T1, 'list_img')

    # avererge if multiple T2
    av_T2 = pe.Node(niu.Function(
        input_names=['list_img'],
        output_names=['avg_img'],
        function=average_align), name="av_T2")

    data_preparation_pipe.connect(inputnode, 'T2', av_T2, 'list_img')

    if "reorient" in params.keys():

        if "new_dims" in params["reorient"].keys():
            new_dims = tuple(params["reorient"]["new_dims"].split())

        else:
            new_dims = ("x", "z", "-y")

        reorient_T1_pipe = _create_reorient_pipeline(
            name="reorient_T1_pipe", new_dims=new_dims)

        data_preparation_pipe.connect(av_T1, 'avg_img',
                                      reorient_T1_pipe, 'inputnode.image')

        reorient_T2_pipe = _create_reorient_pipeline(
            name="reorient_T2_pipe", new_dims=new_dims)
        data_preparation_pipe.connect(av_T2, 'avg_img',
                                      reorient_T2_pipe, 'inputnode.image')

    if "crop" in params.keys():
        print('crop is in params')

        # align avg T2 on avg T1
        align_T2_on_T1 = pe.Node(fsl.FLIRT(), name="align_T2_on_T1")
        align_T2_on_T1.inputs.dof = 6

        # cropping
        # Crop bounding box for T1
        crop_bb_T1 = NodeParams(fsl.ExtractROI(),
                                params=parse_key(params, "crop"),
                                name='crop_bb_T1')

        data_preparation_pipe.connect(
            inputnode, ('indiv_params', parse_key, "crop"),
            crop_bb_T1, 'indiv_params')

        # Crop bounding box for T2
        crop_bb_T2 = NodeParams(fsl.ExtractROI(),
                                params=parse_key(params, "crop"),
                                name='crop_bb_T2')

        data_preparation_pipe.connect(
            inputnode, ('indiv_params', parse_key, "crop"),
            crop_bb_T2, 'indiv_params')

        # Crop bounding box for T2
        if "reorient" in params.keys():
            data_preparation_pipe.connect(reorient_T1_pipe,
                                          'swap_dim.out_file',
                                          align_T2_on_T1, 'reference')
            data_preparation_pipe.connect(reorient_T2_pipe,
                                          'swap_dim.out_file',
                                          align_T2_on_T1, 'in_file')

            data_preparation_pipe.connect(reorient_T1_pipe,
                                          'swap_dim.out_file',
                                          crop_bb_T1, 'in_file')
        else:
            data_preparation_pipe.connect(av_T1, 'avg_img',
                                          align_T2_on_T1, 'reference')
            data_preparation_pipe.connect(av_T2, 'avg_img',
                                          align_T2_on_T1, 'in_file')
            data_preparation_pipe.connect(av_T1, 'avg_img',
                                          crop_bb_T1, 'in_file')

        data_preparation_pipe.connect(align_T2_on_T1, "out_file",
                                      crop_bb_T2, 'in_file')

    elif "bet_crop" in params.keys():

        print('bet_crop is in params')

        # Align, Brain extraction + Cropping
        bet_crop = NodeParams(T1xT2BET(),
                              params=parse_key(params, "bet_crop"),
                              name='bet_crop')

        data_preparation_pipe.connect(
            inputnode, ('indiv_params', parse_key, "bet_crop"),
            bet_crop, 'indiv_params')

        if "reorient" in params.keys():

            data_preparation_pipe.connect(reorient_T1_pipe,
                                          'swap_dim.out_file',
                                          bet_crop, 't1_file')
            data_preparation_pipe.connect(reorient_T2_pipe,
                                          'swap_dim.out_file',
                                          bet_crop, 't2_file')
        else:
            data_preparation_pipe.connect(av_T1, 'avg_img',
                                          bet_crop, 't1_file')
            data_preparation_pipe.connect(av_T2, 'avg_img',
                                          bet_crop, 't2_file')

    else:
        print("No bet_crop parameters, or no individual cropping were found, \
            align T1 and T2 is performed")

        # align avg T2 on avg T1
        align_T2_on_T1 = pe.Node(fsl.FLIRT(), name="align_T2_on_T1")
        align_T2_on_T1.inputs.dof = 6

        if "reorient" in params.keys():

            data_preparation_pipe.connect(reorient_T1_pipe,
                                          'swap_dim.out_file',
                                          align_T2_on_T1, 'reference')
            data_preparation_pipe.connect(reorient_T2_pipe,
                                          'swap_dim.out_file',
                                          align_T2_on_T1, 'in_file')
        else:
            data_preparation_pipe.connect(av_T1, 'avg_img',
                                          align_T2_on_T1, 'reference')
            data_preparation_pipe.connect(av_T2, 'avg_img',
                                          align_T2_on_T1, 'in_file')

    # denoise with Ants package
    denoise_T1 = pe.Node(interface=DenoiseImage(), name="denoise_T1")
    denoise_T2 = pe.Node(interface=DenoiseImage(), name="denoise_T2")

    if "bet_crop" in params.keys():
        data_preparation_pipe.connect(bet_crop, "t1_cropped_file",
                                      denoise_T1, 'input_image')
        data_preparation_pipe.connect(bet_crop, "t2_cropped_file",
                                      denoise_T2, 'input_image')

    elif "crop" in params.keys():
        data_preparation_pipe.connect(crop_bb_T1, "roi_file",
                                      denoise_T1, 'input_image')
        data_preparation_pipe.connect(crop_bb_T2, "roi_file",
                                      denoise_T2, 'input_image')

    # Creating output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['preproc_T1', 'preproc_T2']),
        name='outputnode'
    )

    data_preparation_pipe.connect(denoise_T1, 'output_image',
                                  outputnode, 'preproc_T1')

    data_preparation_pipe.connect(denoise_T2, 'output_image',
                                  outputnode, 'preproc_T2')

    return data_preparation_pipe


###############################################################################
# BABOON TEST (mapnode)
###############################################################################
def _create_mapnode_reorient_pipeline(name="reorient_pipe",
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
        niu.IdentityInterface(fields=['list_img']),
        name='inputnode'
    )

    swap_dim = pe.MapNode(fsl.SwapDimensions(new_dims=new_dims),
                          name="swap_dim", iterfield=["in_file"])
    reorient_pipe.connect(inputnode, 'list_img', swap_dim, 'in_file')

    deorient = pe.MapNode(FslOrient(main_option="deleteorient"),
                          name="deorient", iterfield=["in_file"])
    reorient_pipe.connect(swap_dim, 'out_file', deorient, 'in_file')

    reorient = pe.MapNode(FslOrient(main_option="setqformcode", code=1),
                          name="reorient", iterfield=["in_file"])
    reorient_pipe.connect(deorient, 'out_file', reorient, 'in_file')

    return reorient_pipe


def _create_mapnode_prep_pipeline(params, name="mapnode_prep_pipeline"):

    # init pipeline
    mapnode_prep_pipeline = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['list_img']),
        name='inputnode')

    # Reorient if needed
    if "reorient" in params.keys():

        if "new_dims" in params["reorient"].keys():
            new_dims = tuple(params["reorient"]["new_dims"].split())

        else:
            new_dims = ("x", "z", "-y")

            reorient_pipe = _create_mapnode_reorient_pipeline(
                name="reorient_pipe", new_dims=new_dims)

            mapnode_prep_pipeline.connect(inputnode, 'list_img',
                                          reorient_pipe, 'inputnode.list_img')

    # denoise with Ants package
    # (taking into account whether reorient has been performed or not)
    denoise = MapNodeParams(interface=DenoiseImage(),
                            params=parse_key(params, "denoise"),
                            name="denoise",
                            iterfield=["input_image"])

    if "reorient" in params.keys():
        mapnode_prep_pipeline.connect(reorient_pipe, 'swap_dim.out_file',
                                      denoise, 'input_image')
    else:
        mapnode_prep_pipeline.connect(inputnode, 'list_img',
                                      denoise, 'input_image')

    # cropping
    crop_bb = MapNodeParams(fsl.ExtractROI(),
                            params=parse_key(params, "crop"),
                            name='crop_bb',
                            iterfield=["in_file"])

    mapnode_prep_pipeline.connect(denoise, 'output_image',
                                  crop_bb, 'in_file')

    # N4 intensity normalization with parameters from json
    norm_intensity = MapNodeParams(ants.N4BiasFieldCorrection(),
                                   params=parse_key(params, "norm_intensity"),
                                   name='norm_intensity',
                                   iterfield=['input_image'])

    mapnode_prep_pipeline.connect(crop_bb, 'roi_file',
                                  norm_intensity, "input_image")

    return mapnode_prep_pipeline


def create_data_mapnode_preparation_pipe(params,
                                         name="data_mapnode_preparation_pipe"):
    """
    prepare:
    - reorient if needed (makes the whole pipeline more neat)
    - start by denoising all input images ->
         so we dont have to keep repeating it
         if we are testing other parameters in dataprep (e.g. cropping)
    - crop T1 and T2 based on individual parameters
    - running N4biascorrection on cropped T1 and T2
         -> to help T2 and T1 alignment
    - align T2 to T1
    """

    # creating pipeline
    data_mapnode_preparation_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1', 'T2', 'indiv_params']),
        name='inputnode'
    )

    # mapnode_prep_pipeline for T1 list
    mapnode_prep_T1_pipe = _create_mapnode_prep_pipeline(
        params=parse_key(params, "mapnode_prep_T1"),
        name="mapnode_prep_T1")

    data_mapnode_preparation_pipe.connect(
        inputnode, 'T1', mapnode_prep_T1_pipe, "inputnode.list_img")

    # average if multiple T1
    av_T1 = pe.Node(
        niu.Function(input_names=['list_img'],
                     output_names=['avg_img'],
                     function=average_align),
        name="av_T1")

    data_mapnode_preparation_pipe.connect(
        mapnode_prep_T1_pipe, 'norm_intensity.output_image', av_T1, 'list_img')

    # mapnode_prep_pipeline for T2 list
    mapnode_prep_T2_pipe = _create_mapnode_prep_pipeline(
        params=parse_key(params, "mapnode_prep_T2"),
        name="mapnode_prep_T2")

    data_mapnode_preparation_pipe.connect(
        inputnode, 'T2', mapnode_prep_T2_pipe, "inputnode.list_img")

    # average if multiple T2
    av_T2 = pe.Node(
        niu.Function(input_names=['list_img'],
                     output_names=['avg_img'],
                     function=average_align),
        name="av_T2")

    data_mapnode_preparation_pipe.connect(
        mapnode_prep_T2_pipe, 'norm_intensity.output_image', av_T2, 'list_img')

    # align T2 on T1 - mutualinfo works better for crossmodal biased images
    align_T2_on_T1 = NodeParams(fsl.FLIRT(),
                                params=parse_key(params, "align_T2_on_T1"),
                                name="align_T2_on_T1")

    data_mapnode_preparation_pipe.connect(av_T1, 'avg_img',
                                          align_T2_on_T1, 'reference')
    data_mapnode_preparation_pipe.connect(av_T2, 'avg_img',
                                          align_T2_on_T1, 'in_file')

    # Creating output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['preproc_T1', 'preproc_T2']),
        name='outputnode')

    data_mapnode_preparation_pipe.connect(av_T1, 'avg_img',
                                          outputnode, 'preproc_T1')
    data_mapnode_preparation_pipe.connect(align_T2_on_T1, 'out_file',
                                          outputnode, 'preproc_T2')

    return data_mapnode_preparation_pipe
