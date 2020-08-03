
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.ants as ants

from nipype.interfaces.ants.segmentation import DenoiseImage

from ..utils.utils_nodes import NodeParams, MapNodeParams, ParseParams
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


def _create_prep_pipeline(params, name="prep_pipeline"):

    # init pipeline
    prep_pipeline = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['img', 'indiv_params']),
        name='inputnode')

    parse_params = pe.Node(ParseParams(), name="parse_params")
    parse_params.inputs.key = name

    prep_pipeline.connect(inputnode, "indiv_params", parse_params, "params")

    # Reorient if needed
    if "reorient" in params.keys():

        if "new_dims" in params["reorient"].keys():
            new_dims = tuple(params["reorient"]["new_dims"].split())

        else:
            new_dims = ("x", "z", "-y")

            reorient_pipe = _create_reorient_pipeline(
                name="reorient_pipe", new_dims=new_dims)

            prep_pipeline.connect(inputnode, 'img',
                                  reorient_pipe, 'inputnode.img')

    if "denoise_first" in params.keys():
        # denoise with Ants package
        # (taking into account whether reorient has been performed or not)
        denoise_first = NodeParams(interface=DenoiseImage(),
                                   params=parse_key(params, "denoise"),
                                   name="denoise")

        if "reorient" in params.keys():
            prep_pipeline.connect(reorient_pipe, 'swap_dim.out_file',
                                  denoise_first, 'input_image')
        else:
            prep_pipeline.connect(inputnode, 'img',
                                  denoise_first, 'input_image')
        prep_pipeline.connect(
            parse_params, ('parsed_params', parse_key, "denoise_first"),
            denoise_first, 'indiv_params')

    # cropping
    crop = NodeParams(fsl.ExtractROI(), params=parse_key(params, "crop"),
                      name='crop')

    if "denoise_first" in params.keys():
        prep_pipeline.connect(denoise_first, 'output_image',
                              crop, 'in_file')
    elif "reorient" in params.keys():
        prep_pipeline.connect(reorient_pipe, 'swap_dim.out_file',
                              crop, 'in_file')
    else:
        prep_pipeline.connect(inputnode, 'img',
                              crop, 'in_file')
    prep_pipeline.connect(
        parse_params, ('parsed_params', parse_key, "crop"),
        crop, 'indiv_params')

    # N4 intensity normalization with parameters from json
    norm_intensity = NodeParams(ants.N4BiasFieldCorrection(),
                                params=parse_key(params, "norm_intensity"),
                                name='norm_intensity')

    prep_pipeline.connect(crop, 'roi_file',
                                norm_intensity, "input_image")
    prep_pipeline.connect(
        parse_params, ('parsed_params', parse_key, "norm_intensity"),
        norm_intensity, 'indiv_params')

    if "denoise" in params.keys():

        # denoise with Ants package
        # (taking into account whether reorient has been performed or not)
        denoise = NodeParams(interface=DenoiseImage(),
                             params=parse_key(params, "denoise"),
                             name="denoise")

        prep_pipeline.connect(norm_intensity, "output_image",
                              denoise, 'input_image')
        prep_pipeline.connect(
            parse_params, ('parsed_params', parse_key, "denoise"),
            denoise, 'indiv_params')

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['prep_img']),
        name='outputnode')

    if "denoise" in params.keys():

        prep_pipeline.connect(denoise, 'output_image',
                              outputnode, "prep_img")

    else:

        prep_pipeline.connect(norm_intensity, "output_image",
                              outputnode, "prep_img")

    return prep_pipeline


def _create_mapnode_prep_pipeline(params, name="mapnode_prep_pipeline"):

    # init pipeline
    mapnode_prep_pipeline = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['list_img', 'indiv_params']),
        name='inputnode')

    parse_params = pe.Node(ParseParams(), name="parse_params")
    parse_params.inputs.key = name

    mapnode_prep_pipeline.connect(inputnode, "indiv_params",
                                  parse_params, "params")

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

    if "denoise_first" in params.keys():

        # denoise_first with Ants package
        # (taking into account whether reorient has been performed or not)
        denoise_first = MapNodeParams(
            interface=DenoiseImage(),
            params=parse_key(params, "denoise_first"), name="denoise_first",
            iterfield=["input_image"])

        if "reorient" in params.keys():
            mapnode_prep_pipeline.connect(reorient_pipe, 'swap_dim.out_file',
                                          denoise_first, 'input_image')
        else:
            mapnode_prep_pipeline.connect(inputnode, 'list_img',
                                          denoise_first, 'input_image')
        mapnode_prep_pipeline.connect(
            parse_params, ('parsed_params', parse_key, "denoise_first"),
            denoise_first, 'indiv_params')

    # cropping
    crop = MapNodeParams(fsl.ExtractROI(),  params=parse_key(params, "crop"),
                         name='crop', iterfield=["in_file"])

    if "denoise_first" in params.keys():
        mapnode_prep_pipeline.connect(denoise_first, 'output_image',
                                      crop, 'in_file')
    elif "reorient" in params.keys():
        mapnode_prep_pipeline.connect(reorient_pipe, 'swap_dim.out_file',
                                      crop, 'in_file')
    else:
        mapnode_prep_pipeline.connect(inputnode, 'list_img',
                                      crop, 'in_file')
    mapnode_prep_pipeline.connect(
        parse_params, ('parsed_params', parse_key, "crop"),
        crop, 'indiv_params')

    # N4 intensity normalization with parameters from json
    norm_intensity = MapNodeParams(ants.N4BiasFieldCorrection(),
                                   params=parse_key(params, "norm_intensity"),
                                   name='norm_intensity',
                                   iterfield=['input_image'])

    mapnode_prep_pipeline.connect(crop, 'roi_file',
                                  norm_intensity, "input_image")
    mapnode_prep_pipeline.connect(
        parse_params, ('parsed_params', parse_key, "norm_intensity"),
        norm_intensity, 'indiv_params')

    if "denoise" in params.keys():

        # denoise with Ants package
        # (taking into account whether reorient has been performed or not)
        denoise = MapNodeParams(interface=DenoiseImage(),
                                params=parse_key(params, "denoise"),
                                name="denoise",
                                iterfield=["input_image"])

        mapnode_prep_pipeline.connect(norm_intensity, "output_image",
                                      denoise, "input_image")
        mapnode_prep_pipeline.connect(
            parse_params, ('parsed_params', parse_key, "denoise"),
            denoise, 'indiv_params')

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['prep_list_img']),
        name='outputnode')

    if "denoise" in params.keys():

        mapnode_prep_pipeline.connect(denoise, "output_image",
                                      outputnode, "prep_list_img")

    else:

        mapnode_prep_pipeline.connect(norm_intensity, "output_image",
                                      outputnode, "prep_list_img")

    return mapnode_prep_pipeline


###############################################################################
# choices between the 3 main pipelines: "short", "long_single" et "long_multi"
###############################################################################
def create_short_preparation_pipe(params, name="short_preparation_pipe"):

    """Description: old data preparation:, T1s and T2s are averaged
    (by modality) and then average imgs are processed:

    - reorient (opt: reorient) makes the whole pipeline more neat)

    - bet_crop (include alignement, and mask generation)

    - denoising all input images (opt: denoise in json))


    Inputs:

        inputnode:
            list_T1: T1 files (from BIDSDataGrabber)
            list_T2: T2 files
            indiv_params (opt): dict with individuals parameters for some nodes

        arguments:
            params: dictionary of node sub-parameters (from a json file)
            name: pipeline name (default = "long_multi_preparation_pipe")

    Outputs:

        outputnode:
            preproc_T1: preprocessed T1 file
            preproc_T2: preprocessed T2 file
    """

    # creating pipeline
    data_preparation_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['list_T1', 'list_T2', 'indiv_params']),
        name='inputnode'
    )

    # avererge if multiple T2
    av_T2 = pe.Node(niu.Function(
        input_names=['list_img'],
        output_names=['avg_img'],
        function=average_align), name="av_T2")
    data_preparation_pipe.connect(inputnode, 'list_T2', av_T2, 'list_img')

    # avererge if multiple T1
    av_T1 = pe.Node(
        niu.Function(input_names=['list_img'],
                     output_names=['avg_img'],
                     function=average_align),
        name="av_T1")
    data_preparation_pipe.connect(inputnode, 'list_T1', av_T1, 'list_img')

    if "reorient" in params.keys():
        print('reorient is in params')

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

    if "bet_crop" in params.keys():
        print('bet_crop is in params')

        # Brain extraction (unused) + Cropping
        bet_crop = NodeParams(T1xT2BET(), params=params["bet_crop"],
                              name='bet_crop')

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

    elif "crop" in params.keys():
        print('crop is in params')

        assert "args" in params["crop"].keys(), \
            "Error, args is not specified for crop node, breaking"

        # align avg T2 on avg T1
        align_T2_on_T1 = pe.Node(fsl.FLIRT(), name="align_T2_on_T1")
        align_T2_on_T1.inputs.dof = 6

        # cropping
        # Crop bounding box for T1
        crop_T1 = NodeParams(fsl.ExtractROI(),
                             params=parse_key(params, 'crop'),
                             name='crop_T1')

        # Crop bounding box for T2
        crop_T2 = NodeParams(fsl.ExtractROI(),
                             params=parse_key(params, 'crop'),
                             name='crop_T2')

        if "reorient" in params.keys():
            data_preparation_pipe.connect(reorient_T1_pipe,
                                          'swap_dim.out_file',
                                          align_T2_on_T1, 'reference')
            data_preparation_pipe.connect(reorient_T2_pipe,
                                          'swap_dim.out_file',
                                          align_T2_on_T1, 'in_file')

            data_preparation_pipe.connect(reorient_T1_pipe,
                                          'swap_dim.out_file',
                                          crop_T1, 'in_file')
        else:
            data_preparation_pipe.connect(av_T1, 'avg_img',
                                          align_T2_on_T1, 'reference')
            data_preparation_pipe.connect(av_T2, 'avg_img',
                                          align_T2_on_T1, 'in_file')
            data_preparation_pipe.connect(av_T1, 'avg_img',
                                          crop_T1, 'in_file')

        data_preparation_pipe.connect(align_T2_on_T1, "out_file",
                                      crop_T2, 'in_file')

    # denoise with Ants package
    denoise_T1 = NodeParams(interface=DenoiseImage(),
                            params=parse_key(params, "denoise"),
                            name="denoise_T1")
    denoise_T2 = NodeParams(interface=DenoiseImage(),
                            params=parse_key(params, "denoise"),
                            name="denoise_T2")

    if "bet_crop" in params.keys():
        data_preparation_pipe.connect(bet_crop, "t1_cropped_file",
                                      denoise_T1, 'input_image')
        data_preparation_pipe.connect(bet_crop, "t2_cropped_file",
                                      denoise_T2, 'input_image')

    elif "crop" in params.keys():
        data_preparation_pipe.connect(crop_T1, "roi_file",
                                      denoise_T1, 'input_image')
        data_preparation_pipe.connect(crop_T2, "roi_file",
                                      denoise_T2, 'input_image')

    # Creating output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['preproc_T1', 'preproc_T2']),
        name='outputnode')

    data_preparation_pipe.connect(denoise_T1, 'output_image',
                                  outputnode, 'preproc_T1')

    data_preparation_pipe.connect(denoise_T2, 'output_image',
                                  outputnode, 'preproc_T2')

    return data_preparation_pipe


def create_long_single_preparation_pipe(params,
                                        name="long_single_preparation_pipe"):
    """Description: Short data preparation, T1s and T2s are averaged
    (by modality) and then average imgs are processed:

    - reorient (opt: reorient) makes the whole pipeline more neat)

    - start by denoising all input images (opt: denoise_first in json)

    - crop T1 and T2 based on individual parameters

    - running N4biascorrection on cropped T1 and T to help T2 and T1 alignment

    - finish by denoising all input images (opt: denoise in json))

    - Finally, align T2 to T1

    Inputs:

        inputnode:
            list_T1: T1 files (from BIDSDataGrabber)
            list_T2: T2 files
            indiv_params (opt): dict with individuals parameters for some nodes

        arguments:
            params: dictionary of node sub-parameters (from a json file)
            name: pipeline name (default = "long_multi_preparation_pipe")

    Outputs:

        outputnode:
            preproc_T1: preprocessed T1 file
            preproc_T2: preprocessed T2 file

    """

    # creating pipeline
    long_single_preparation_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['list_T1', 'list_T2', 'indiv_params']),
        name='inputnode'
    )

    # average if multiple T1
    av_T1 = pe.Node(
        niu.Function(input_names=['list_img'],
                     output_names=['avg_img'],
                     function=average_align),
        name="av_T1")

    long_single_preparation_pipe.connect(
        inputnode, 'list_T1', av_T1, "list_img")

    # list_prep_pipeline for T1 list
    prep_T1_pipe = _create_prep_pipeline(
        params=parse_key(params, "prep_T1"),
        name="prep_T1")

    long_single_preparation_pipe.connect(
        av_T1, 'avg_img', prep_T1_pipe, "inputnode.img")

    long_single_preparation_pipe.connect(inputnode, 'indiv_params',
                                         prep_T1_pipe,
                                         "inputnode.indiv_params")

    # average if multiple T2
    av_T2 = pe.Node(
        niu.Function(input_names=['list_img'],
                     output_names=['avg_img'],
                     function=average_align),
        name="av_T2")

    long_single_preparation_pipe.connect(
        inputnode, 'list_T2', av_T2, "list_img")

    # list_prep_pipeline for T2 list
    prep_T2_pipe = _create_prep_pipeline(
        params=parse_key(params, "prep_T2"),
        name="prep_T2")

    long_single_preparation_pipe.connect(
        av_T2, 'avg_img', prep_T2_pipe, "inputnode.img")

    long_single_preparation_pipe.connect(inputnode, 'indiv_params',
                                         prep_T2_pipe,
                                         "inputnode.indiv_params")

    # align T2 on T1 - mutualinfo works better for crossmodal biased images
    align_T2_on_T1 = NodeParams(fsl.FLIRT(),
                                params=parse_key(params, "align_T2_on_T1"),
                                name="align_T2_on_T1")

    long_single_preparation_pipe.connect(prep_T1_pipe, 'outputnode.prep_img',
                                         align_T2_on_T1, 'reference')
    long_single_preparation_pipe.connect(prep_T2_pipe, 'outputnode.prep_img',
                                         align_T2_on_T1, 'in_file')

    # Creating output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['preproc_T1', 'preproc_T2']),
        name='outputnode')

    long_single_preparation_pipe.connect(prep_T1_pipe, 'outputnode.prep_img',
                                         outputnode, 'preproc_T1')
    long_single_preparation_pipe.connect(align_T2_on_T1, 'out_file',
                                         outputnode, 'preproc_T2')

    return long_single_preparation_pipe


def create_long_multi_preparation_pipe(params,
                                       name="long_multi_preparation_pipe"):
    """Description: long data preparation,
    each T1 and T2 is processed independantly with:

    - reorient (opt: reorient) makes the whole pipeline more neat)

    - start by denoising all input images (opt: denoise_first in json)

    - crop T1 and T2 based on individual parameters

    - running N4biascorrection on cropped T1 and T to help T2 and T1 alignment

    - finish by denoising all input images (opt: denoise in json))

    - processed T1s and T2s are averaged (by modality)

    - Finally, align average T2 to average T1

    Inputs:

        inputnode:
            list_T1: T1 files (from BIDSDataGrabber)

            list_T2: T2 files

            indiv_params (opt): dict with individuals parameters for some nodes

        arguments:
            params: dictionary of node sub-parameters (from a json file)

            name: pipeline name (default = "long_multi_preparation_pipe")

    Outputs:

        outputnode:
            preproc_T1: preprocessed T1 file

            preproc_T2: preprocessed T2 file

    """

    # creating pipeline
    long_multi_preparation_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['list_T1', 'list_T2', 'indiv_params']),
        name='inputnode'
    )

    # Creating output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['preproc_T1', 'preproc_T2']),
        name='outputnode')

    # mapnode_prep_pipeline for T1 list
    mapnode_prep_T1_pipe = _create_mapnode_prep_pipeline(
        params=parse_key(params, "mapnode_prep_T1"),
        name="mapnode_prep_T1")

    long_multi_preparation_pipe.connect(
        inputnode, 'list_T1', mapnode_prep_T1_pipe, "inputnode.list_img")

    long_multi_preparation_pipe.connect(
        inputnode, 'indiv_params',
        mapnode_prep_T1_pipe, "inputnode.indiv_params")

    # average if multiple T1
    av_T1 = pe.Node(
        niu.Function(input_names=['list_img'],
                     output_names=['avg_img'],
                     function=average_align),
        name="av_T1")

    long_multi_preparation_pipe.connect(
        mapnode_prep_T1_pipe, 'outputnode.prep_list_img', av_T1, 'list_img')

    # mapnode_prep_pipeline for T2 list
    mapnode_prep_T2_pipe = _create_mapnode_prep_pipeline(
        params=parse_key(params, "mapnode_prep_T2"),
        name="mapnode_prep_T2")

    long_multi_preparation_pipe.connect(
        inputnode, 'list_T2', mapnode_prep_T2_pipe, "inputnode.list_img")

    long_multi_preparation_pipe.connect(
        inputnode, 'indiv_params',
        mapnode_prep_T2_pipe, "inputnode.indiv_params")

    # average if multiple T2
    av_T2 = pe.Node(
        niu.Function(input_names=['list_img'],
                     output_names=['avg_img'],
                     function=average_align),
        name="av_T2")

    long_multi_preparation_pipe.connect(
        mapnode_prep_T2_pipe, 'outputnode.prep_list_img', av_T2, 'list_img')

    # align T2 on T1 - mutualinfo works better for crossmodal biased images
    align_T2_on_T1 = NodeParams(fsl.FLIRT(),
                                params=parse_key(params, "align_T2_on_T1"),
                                name="align_T2_on_T1")

    long_multi_preparation_pipe.connect(av_T1, 'avg_img',
                                        align_T2_on_T1, 'reference')
    long_multi_preparation_pipe.connect(av_T2, 'avg_img',
                                        align_T2_on_T1, 'in_file')

    # output node
    long_multi_preparation_pipe.connect(av_T1, 'avg_img',
                                        outputnode, 'preproc_T1')
    long_multi_preparation_pipe.connect(align_T2_on_T1, 'out_file',
                                        outputnode, 'preproc_T2')

    return long_multi_preparation_pipe
