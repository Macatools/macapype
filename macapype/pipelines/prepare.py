
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl

from nipype.interfaces.niftyreg import reg

from nipype.interfaces.niftyreg import regutils

from nipype.interfaces.ants.segmentation import DenoiseImage

from ..utils.utils_nodes import NodeParams, MapNodeParams
from ..utils.misc import parse_key

from ..nodes.prepare import average_align, FslOrient


# should be in nipype code directly
from ..nodes.prepare import Refit


def _create_avg_reorient_pipeline(name="avg_reorient_pipe", params={}):
    """
    By david:
    average_align
    3drefit -deoblique -origin LSP image_good.nii.gz;
    fslreorient2std image_good.nii.gz
    """

    # creating pipeline
    reorient_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['list_img', 'indiv_params']),
        name='inputnode'
    )

    average_img = pe.Node(
        niu.Function(input_names=['list_img'],
                     output_names=['avg_img'],
                     function=average_align),
        name="average_img")

    reorient_pipe.connect(inputnode, 'list_img', average_img, 'list_img')

    # Refit
    reorient = NodeParams(Refit(),
                          params=parse_key(params, "reorient"),
                          name="reorient")

    reorient_pipe.connect(average_img, 'avg_img', reorient, 'in_file')

    reorient_pipe.connect(inputnode, ('indiv_params', parse_key, 'reorient'),
                          reorient, 'indiv_params')

    # Reorient2std
    std_img = pe.Node(fsl.Reorient2Std(), name="std_img")

    reorient_pipe.connect(reorient, "out_file", std_img, 'in_file')

    outputnode = pe.Node(niu.IdentityInterface(fields=['avg_img', 'std_img']),
                         name="outputnode")

    reorient_pipe.connect(std_img, 'out_file', outputnode, 'std_img')

    return reorient_pipe


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
    By kepkee (mapnode):
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


def _create_prep_pipeline(params, name="prep_pipeline", node_suffix=""):
    """Description: hidden function for sequence of preprocessing

    Params:

    - reorient (new dims as a string (e.g. "x z -y"))
    - crop (see `ExtractROI <https://nipype.readthedocs.io/en/0.12.1/\
    interfaces/generated/nipype.interfaces.fsl.utils.html#extractroi>`_ \
    for arguments) - also available as :ref:`indiv_params <indiv_params>`
    - denoise (see `DenoiseImage <https://nipype.readthedocs.io/en/0.12.\
    1/interfaces/generated/nipype.interfaces.ants.segmentation.html\
    #denoiseimage>`_ for arguments)) - also available \
    as :ref:`indiv_params <indiv_params>`
    """

    # init pipeline
    prep_pipeline = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['img', 'indiv_params']),
        name='inputnode')

    # Reorient if needed
    if "reorient" in params.keys():
        print("adding reorient pipeline")
        if "new_dims" in params["reorient"].keys():
            new_dims = tuple(params["reorient"]["new_dims"].split())
            print("using new dim")
        else:
            new_dims = ("x", "z", "-y")

        reorient_pipe = _create_reorient_pipeline(
            name="reorient_pipe", new_dims=new_dims)

        prep_pipeline.connect(inputnode, 'img',
                              reorient_pipe, 'inputnode.image')

    # cropping
    if 'crop'+node_suffix not in params.keys():
        print("Error, crop"+node_suffix+" could be found in params")
        print("Breaking")

        exit(0)

    crop = NodeParams(fsl.ExtractROI(),
                      params=parse_key(params, "crop"+node_suffix),
                      name='crop'+node_suffix)

    if "reorient" in params.keys():
        prep_pipeline.connect(reorient_pipe, 'reorient.out_file',
                              crop, 'in_file')
    else:
        prep_pipeline.connect(inputnode, 'img',
                              crop, 'in_file')
    prep_pipeline.connect(
        inputnode, ('indiv_params', parse_key, "crop"+node_suffix),
        crop, 'indiv_params')

    if "denoise" in params.keys():

        # denoise with Ants package
        # (taking into account whether reorient has been performed or not)
        denoise = NodeParams(interface=DenoiseImage(),
                             params=parse_key(params, "denoise"),
                             name="denoise")

        prep_pipeline.connect(crop, 'roi_file',
                              denoise, 'input_image')
        prep_pipeline.connect(
            inputnode, ('indiv_params', parse_key, "denoise"),
            denoise, 'indiv_params')

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['prep_img']),
        name='outputnode')

    if "denoise" in params.keys():

        prep_pipeline.connect(denoise, 'output_image',
                              outputnode, "prep_img")

    else:

        prep_pipeline.connect(crop, 'roi_file',
                              outputnode, "prep_img")

    return prep_pipeline


def _create_mapnode_prep_pipeline(params, name="mapnode_prep_pipeline",
                                  node_suffix=""):

    """Description: hidden function for sequence of preprocessing (mapnode)

    Params: (Warning: **all arguments are in lists**)

    - reorient (new dims as a string (e.g. "x z -y"))
    - crop (see `ExtractROI <https://nipype.readthedocs.io/en/0.12.1/\
    interfaces/generated/nipype.interfaces.fsl.utils.html#extractroi>`_ \
    for arguments) - also available as :ref:`indiv_params <indiv_params>`
    - denoise (see `DenoiseImage <https://nipype.readthedocs.io/en/0.12.\
    1/interfaces/generated/nipype.interfaces.ants.segmentation.html\
    #denoiseimage>`_ for arguments)) - also available \
    as :ref:`indiv_params <indiv_params>`
    """

    # init pipeline
    mapnode_prep_pipeline = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['list_img', 'indiv_params']),
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

    if 'crop'+node_suffix not in params.keys():
        print("Error, crop"+node_suffix+" could be found in params")
        print("Breaking")

        exit(0)

    # cropping
    crop = MapNodeParams(fsl.ExtractROI(),
                         params=parse_key(params, "crop"+node_suffix),
                         name='crop', iterfield=["in_file", "args"])

    if "reorient" in params.keys():
        mapnode_prep_pipeline.connect(reorient_pipe, 'reorient.out_file',
                                      crop, 'in_file')
    else:
        mapnode_prep_pipeline.connect(inputnode, 'list_img',
                                      crop, 'in_file')
    mapnode_prep_pipeline.connect(
        inputnode, ('indiv_params', parse_key, "crop"+node_suffix),
        crop, 'indiv_params')

    if "denoise" in params.keys():

        # denoise with Ants package
        # (taking into account whether reorient has been performed or not)
        denoise = MapNodeParams(interface=DenoiseImage(),
                                params=parse_key(params, "denoise"),
                                name="denoise",
                                iterfield=["input_image"])

        mapnode_prep_pipeline.connect(crop, 'roi_file',
                                      denoise, "input_image")

        mapnode_prep_pipeline.connect(
            inputnode, ("indiv_params", parse_key, "denoise"),
            denoise, 'indiv_params')

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['prep_list_img']),
        name='outputnode')

    if "denoise" in params.keys():

        mapnode_prep_pipeline.connect(denoise, "output_image",
                                      outputnode, "prep_list_img")

    else:

        mapnode_prep_pipeline.connect(crop, 'roi_file',
                                      outputnode, "prep_list_img")

    return mapnode_prep_pipeline


###############################################################################
# choices between the 3 main pipelines: "short", "long_single" et "long_multi"
###############################################################################
def create_short_preparation_pipe(params, params_template={},
                                  name="short_preparation_pipe"):
    """Description: short data preparation (average, reorient, crop/betcrop \
    and denoise)

    Processing steps;

    - T1s and T2s are averaged (by modality).
    - reorient (opt) makes the whole pipeline more neat)
    - Cropped (bet_crop include alignement, and mask generation)
    - denoising all images (no denoise_first)

    Params:

    - reorient (optional; new_dims as a string (e.g. "x z -y"))
    - crop (see `ExtractRoi <https://nipype.readthedocs.io/en/0.12.1/inte\
    rfaces/generated/nipype.interfaces.fsl.utils.html#extractroi>`_ for \
    arguments). crop is also available as :ref:`indiv_params <indiv_params>`
    - denoise (see `DenoiseImage <https://\
    nipype.readthedocs.io/en/0.12.1/interfaces/generated/nipype.interfaces\
    .ants.segmentation.html#denoiseimage>`_ for arguments))

    Inputs:

        inputnode:

            list_T1:
                T1 files (from BIDSDataGrabber)

            list_T2:
                T2 files

            indiv_params (opt):
                dict with individuals parameters for some nodes

        arguments:

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "long_multi_preparation_pipe")

    Outputs:

        outputnode:

            preproc_T1:
                preprocessed T1 file

            preproc_T2:
                preprocessed T2 file
    """

    # creating pipeline
    data_preparation_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['list_T1', 'list_T2', 'indiv_params']),
        name='inputnode'
    )

    # Creating output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['native_T1', 'native_T2',
                                      'preproc_T1', 'preproc_T2']),
        name='outputnode')

    if "avg_reorient_pipe" in params.keys():

        print("Found avg_reorient_pipe for av_T1 and av_T2")

        av_T1 = _create_avg_reorient_pipeline(
            name="av_T1", params=parse_key(params, "avg_reorient_pipe"))

        data_preparation_pipe.connect(inputnode, 'list_T1',
                                      av_T1, 'inputnode.list_img')

        data_preparation_pipe.connect(inputnode, 'indiv_params',
                                      av_T1, 'inputnode.indiv_params')

        av_T2 = _create_avg_reorient_pipeline(
            name="av_T2", params=parse_key(params, "avg_reorient_pipe"))

        data_preparation_pipe.connect(inputnode, 'list_T2',
                                      av_T2, 'inputnode.list_img')

        data_preparation_pipe.connect(inputnode, 'indiv_params',
                                      av_T2, 'inputnode.indiv_params')

    else:

        # average if multiple T2
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

    # align avg T2 on avg T1
    if 'aladin_T2_on_T1' in params.keys():

        align_T2_on_T1 = pe.Node(reg.RegAladin(), name="align_T2_on_T1")

        if "avg_reorient_pipe" in params.keys():
            data_preparation_pipe.connect(av_T1, 'outputnode.std_img',
                                          align_T2_on_T1, 'ref_file')

            data_preparation_pipe.connect(av_T2, 'outputnode.std_img',
                                          align_T2_on_T1, 'flo_file')

        else:
            data_preparation_pipe.connect(av_T1, 'avg_img',
                                          align_T2_on_T1, 'ref_file')

            data_preparation_pipe.connect(av_T2, 'avg_img',
                                          align_T2_on_T1, 'flo_file')

    # align avg T2 on avg T1
    else:

        align_T2_on_T1 = pe.Node(fsl.FLIRT(), name="align_T2_on_T1")
        align_T2_on_T1.inputs.dof = 6

        if "avg_reorient_pipe" in params.keys():
            data_preparation_pipe.connect(av_T1, 'outputnode.std_img',
                                          align_T2_on_T1, 'reference')

            data_preparation_pipe.connect(av_T2, 'outputnode.std_img',
                                          align_T2_on_T1, 'in_file')

        else:
            data_preparation_pipe.connect(av_T1, 'avg_img',
                                          align_T2_on_T1, 'reference')

            data_preparation_pipe.connect(av_T2, 'avg_img',
                                          align_T2_on_T1, 'in_file')

    if "crop_T1" in params.keys():
        print('crop_T1 is in params')

        assert "args" in params["crop_T1"].keys(), \
            "Error, args is not specified for crop node, breaking"

        # cropping
        # Crop bounding box for T1
        crop_T1 = NodeParams(fsl.ExtractROI(),
                             params=parse_key(params, 'crop_T1'),
                             name='crop_T1')

        # Crop bounding box for T2
        crop_T2 = NodeParams(fsl.ExtractROI(),
                             params=parse_key(params, 'crop_T1'),
                             name='crop_T2')

        data_preparation_pipe.connect(
            inputnode, ("indiv_params", parse_key, "crop_T1"),
            crop_T1, 'indiv_params')

        data_preparation_pipe.connect(
            inputnode, ("indiv_params", parse_key, "crop_T1"),
            crop_T2, 'indiv_params')

        if "avg_reorient_pipe" in params.keys():
            data_preparation_pipe.connect(av_T1, 'outputnode.std_img',
                                          crop_T1, 'in_file')
        else:
            data_preparation_pipe.connect(av_T1, 'avg_img',
                                          crop_T1, 'in_file')

        if 'aladin_T2_on_T1' in params.keys():
            data_preparation_pipe.connect(align_T2_on_T1, "res_file",
                                          crop_T2, 'in_file')

        else:
            data_preparation_pipe.connect(align_T2_on_T1, "out_file",
                                          crop_T2, 'in_file')

    else:

        if "pre_crop_z_T1" in params.keys():

            print('pre_crop_z_T1')
            pre_crop_z_T1 = NodeParams(
                fsl.RobustFOV(),
                params=parse_key(params, "pre_crop_z_T1"),
                name='pre_crop_z_T1')

            if "avg_reorient_pipe" in params.keys():
                data_preparation_pipe.connect(av_T1, 'outputnode.std_img',
                                              pre_crop_z_T1, 'in_file')

            else:
                data_preparation_pipe.connect(av_T1, 'avg_img',
                                              pre_crop_z_T1, 'in_file')

        print('default crop_aladin_T1 will be run')
        crop_aladin_T1 = NodeParams(reg.RegAladin(),
                                    params=parse_key(params, "crop_aladin_T1"),
                                    name='crop_aladin_T1')

        if "pre_crop_z_T1" in params.keys():
            data_preparation_pipe.connect(pre_crop_z_T1, "out_roi",
                                          crop_aladin_T1, 'flo_file')
        else:
            if "avg_reorient_pipe" in params.keys():
                data_preparation_pipe.connect(av_T1, 'outputnode.std_img',
                                              crop_aladin_T1, 'flo_file')
            else:
                data_preparation_pipe.connect(av_T1, 'avg_img',
                                              crop_aladin_T1, 'flo_file')

        crop_aladin_T1.inputs.ref_file = params_template["template_head"]

        # crop_z_T1
        if "crop_z_T1" in params.keys():
            crop_z_T1 = NodeParams(fsl.RobustFOV(),
                                   params=parse_key(params, "crop_z_T1"),
                                   name='crop_z_T1')

            data_preparation_pipe.connect(crop_aladin_T1, "res_file",
                                          crop_z_T1, 'in_file')

        # apply reg_resample to T2
        apply_crop_aladin_T2 = NodeParams(
            regutils.RegResample(),
            name='apply_crop_aladin_T2')

        if 'aladin_T2_on_T1' in params.keys():
            data_preparation_pipe.connect(align_T2_on_T1, "res_file",
                                          apply_crop_aladin_T2, 'flo_file')

        else:
            data_preparation_pipe.connect(align_T2_on_T1, "out_file",
                                          apply_crop_aladin_T2, 'flo_file')

        data_preparation_pipe.connect(crop_aladin_T1, 'aff_file',
                                      apply_crop_aladin_T2, 'trans_file')

        if "crop_z_T1" in params.keys():
            data_preparation_pipe.connect(crop_z_T1, "out_roi",
                                          apply_crop_aladin_T2, 'ref_file')
        else:
            data_preparation_pipe.connect(crop_aladin_T1, "res_file",
                                          apply_crop_aladin_T2, 'ref_file')

        # compute inv transfo
        inv_tranfo = NodeParams(
            regutils.RegTransform(),
            params=parse_key(params, "inv_transfo_aladin"),
            name='inv_tranfo')

        data_preparation_pipe.connect(crop_aladin_T1, 'aff_file',
                                      inv_tranfo, 'inv_aff_input')

    # outputnode
    if "avg_reorient_pipe" in params.keys():
        data_preparation_pipe.connect(av_T1, 'outputnode.std_img',
                                      outputnode, 'native_T1')
    else:
        data_preparation_pipe.connect(av_T1, 'avg_img',
                                      outputnode, 'native_T1')

    if 'aladin_T2_on_T1' in params.keys():
        data_preparation_pipe.connect(align_T2_on_T1, "res_file",
                                      outputnode, 'native_T2')
    else:
        data_preparation_pipe.connect(align_T2_on_T1, "out_file",
                                      outputnode, 'native_T2')

    # denoise with Ants package
    if "denoise" in params.keys():

        denoise_T1 = NodeParams(interface=DenoiseImage(),
                                params=parse_key(params, "denoise"),
                                name="denoise_T1")

        denoise_T2 = NodeParams(interface=DenoiseImage(),
                                params=parse_key(params, "denoise"),
                                name="denoise_T2")
        # inputs
        if "crop_T1" in params.keys():
            data_preparation_pipe.connect(crop_T1, "roi_file",
                                          denoise_T1, 'input_image')

            data_preparation_pipe.connect(crop_T2, "roi_file",
                                          denoise_T2, 'input_image')

        else:

            if "crop_z_T1" in params.keys():
                data_preparation_pipe.connect(crop_z_T1, "out_roi",
                                              denoise_T1, 'input_image')
            else:
                data_preparation_pipe.connect(crop_aladin_T1, "res_file",
                                              denoise_T1, 'input_image')

            data_preparation_pipe.connect(apply_crop_aladin_T2, 'out_file',
                                          denoise_T2, 'input_image')

        # outputs
        data_preparation_pipe.connect(denoise_T1, 'output_image',
                                      outputnode, 'preproc_T1')

        data_preparation_pipe.connect(denoise_T2, 'output_image',
                                      outputnode, 'preproc_T2')
    else:

        if "crop_T1" in params.keys():
            data_preparation_pipe.connect(crop_T1, "roi_file",
                                          outputnode, 'preproc_T1')

            data_preparation_pipe.connect(crop_T2, "roi_file",
                                          outputnode, 'preproc_T2')

        else:
            if "crop_z_T1" in params.keys():
                data_preparation_pipe.connect(crop_z_T1, "out_roi",
                                              outputnode, 'preproc_T1')
            else:
                data_preparation_pipe.connect(crop_aladin_T1, "res_file",
                                              outputnode, 'preproc_T1')

            data_preparation_pipe.connect(apply_crop_aladin_T2, 'out_file',
                                          outputnode, 'preproc_T2')

    return data_preparation_pipe


def create_long_single_preparation_pipe(params,
                                        name="long_single_preparation_pipe"):
    """Description: Long data preparation, T1s and T2s are averaged
    (by modality) and then average imgs are processed.

    Processing Steps:

    - average imgs (by modality).
    - reorient (opt) makes the whole pipeline more neat)
    - start by denoising all input images (opt: denoise_first in json)
    - crop T1 and T2 based on individual parameters
    - running N4biascorrection on cropped T1 and T to help T2 and T1 alignment
    - finish by denoising all input images (opt: denoise in json))
    - Finally, align T2 to T1

    Params:

    - prep_T1 and prep_T2 (see :class:`_create_prep_pipeline <macapype.\
    pipelines.prepare._create_prep_pipeline>`)
    - align_T2_on_T1 (see `FLIRT <https://nipype.readthedocs.io/en/0.12.1/\
    interfaces/generated/nipype.interfaces.fsl.preprocess.html#flirt>`_ \
    for more arguments)

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
        name="prep_T1", node_suffix="_T1")

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
        name="prep_T2", node_suffix="_T2")

    long_single_preparation_pipe.connect(
        av_T2, 'avg_img', prep_T2_pipe, "inputnode.img")

    long_single_preparation_pipe.connect(inputnode, 'indiv_params',
                                         prep_T2_pipe,
                                         "inputnode.indiv_params")

    align_T2_on_T1 = NodeParams(reg.RegAladin(),
                                params=parse_key(params, "align_T2_on_T1"),
                                name='align_T2_on_T1')

    long_single_preparation_pipe.connect(prep_T1_pipe, 'outputnode.prep_img',
                                         align_T2_on_T1, 'ref_file')
    long_single_preparation_pipe.connect(prep_T2_pipe, 'outputnode.prep_img',
                                         align_T2_on_T1, 'flo_file')

    # Creating output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['preproc_T1', 'preproc_T2',
                                      "native_T1", "native_T2"]),
        name='outputnode')

    # outputnode
    long_single_preparation_pipe.connect(prep_T1_pipe, 'outputnode.prep_img',
                                         outputnode, 'preproc_T1')

    long_single_preparation_pipe.connect(align_T2_on_T1, 'res_file',
                                         outputnode, 'preproc_T2')

    long_single_preparation_pipe.connect(av_T1, 'avg_img',
                                         outputnode, 'native_T1')

    long_single_preparation_pipe.connect(av_T2, "avg_img",
                                         outputnode, 'native_T2')

    return long_single_preparation_pipe


def create_long_multi_preparation_pipe(params,
                                       name="long_multi_preparation_pipe"):
    """Description: Long data preparation, each T1 and T2 is processed \
    independantly (mapnode).

    Processing steps:

    - reorient (opt: reorient) makes the whole pipeline more neat)
    - start by denoising all input images (opt: denoise_first in json)
    - crop T1 and T2 based on individual parameters
    - running N4biascorrection on cropped T1 and T to help T2 and T1 alignment
    - finish by denoising all input images (opt: denoise in json))
    - processed T1s and T2s are averaged (by modality)
    - Finally, align average T2 to average T1

    Params:

    - mapnode_prep_T1 and mapnodes_prep_T2 (see \
    :class:`_create_mapnode_prep_pipeline \
    <macapype.pipelines.prepare._create_mapnode_prep_pipeline>` for arguments)
    - align_T2_on_T1 (see `FLIRT <https://nipype.readthedocs.io/en/0.12.1/\
    interfaces/generated/nipype.interfaces.fsl.preprocess.html#flirt>`_ \
    for more arguments)

    Inputs:

        inputnode:

            list_T1:
                T1 files (from BIDSDataGrabber)

            list_T2:
                T2 files

            indiv_params (opt):
                dict with individuals parameters for some nodes

        arguments:

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "long_multi_preparation_pipe")

    Outputs:

        :outputnode:

            preproc_T1:
                preprocessed T1 file

            preproc_T2:
                preprocessed T2 file

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
        params=parse_key(params, "prep_T1"),
        name="prep_T1", node_suffix="_T1")

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
        params=parse_key(params, "prep_T2"),
        name="prep_T2", node_suffix="_T2")

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


###############################################################################
# works with only one T1
def create_short_preparation_T1_pipe(params, params_template,
                                     name="short_preparation_T1_pipe"):
    """Description: T1 only short preparation

    Processing steps:

    - T1s and T2s are averaged (by modality).
    - reorient (opt: reorient) makes the whole pipeline more neat)
    - Cropped (bet_crop include alignement, and mask generation)
    - denoising all images (no denoise_first)

    Params:

    - reorient (optional; new_dims as a string (e.g. "x z -y"))
    - bet_crop (:class:`T1xT2BET <macapype.nodes.extract_brain.T1xT2BET>`\
    ) or crop (see `ExtractRoi <https://nipype.readthedocs.io/en/0.12.1/inte\
    rfaces/generated/nipype.interfaces.fsl.utils.html#extractroi>`_ for \
    arguments). crop is also available as :ref:`indiv_params <indiv_params>`
    - denoise (see `DenoiseImage <https://\
    nipype.readthedocs.io/en/0.12.1/interfaces/generated/nipype.interfaces\
    .ants.segmentation.html#denoiseimage>`_ for arguments))

    Inputs:

        inputnode:

            list_T1:
                T1 files (from BIDSDataGrabber)

            indiv_params (opt):
                dict with individuals parameters for some nodes

        arguments:

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "long_multi_preparation_pipe")

    Outputs:

        outputnode:

            preproc_T1:
                preprocessed T1 file

    """

    # creating pipeline
    data_preparation_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['list_T1', 'indiv_params']),
        name='inputnode'
    )

    # Creating output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['preproc_T1', 'native_T1']),
        name='outputnode')

    # average if multiple T1
    if "avg_reorient_pipe" in params.keys():

        av_T1 = _create_avg_reorient_pipeline(
            "av_T1", params=parse_key(params, "avg_reorient_pipe"))

        data_preparation_pipe.connect(inputnode, 'list_T1',
                                      av_T1, 'inputnode.list_img')

        data_preparation_pipe.connect(inputnode, 'indiv_params',
                                      av_T1, 'inputnode.indiv_params')
    else:
        av_T1 = pe.Node(
            niu.Function(input_names=['list_img'],
                         output_names=['avg_img'],
                         function=average_align),
            name="av_T1")
        data_preparation_pipe.connect(inputnode, 'list_T1', av_T1, 'list_img')

    if "crop_T1" in params.keys():
        print('crop_T1 is in params')

        assert "args" in params["crop_T1"].keys(), \
            "Error, args is not specified for crop node, breaking"

        # cropping
        # Crop bounding box for T1
        crop_T1 = NodeParams(fsl.ExtractROI(),
                             params=parse_key(params, 'crop'),
                             name='crop_T1')

        if "avg_reorient_pipe" in params.keys():

            data_preparation_pipe.connect(av_T1,  'outputnode.std_img',
                                          crop_T1, 'in_file')
        else:

            data_preparation_pipe.connect(av_T1,  'avg_img',
                                          crop_T1, 'in_file')

        data_preparation_pipe.connect(
            inputnode, ("indiv_params", parse_key, "crop_T1"),
            crop_T1, 'indiv_params')

    else:

        if "pre_crop_z_T1" in params.keys():

            print('pre_crop_z_T1')
            pre_crop_z_T1 = NodeParams(
                fsl.RobustFOV(),
                params=parse_key(params, "pre_crop_z_T1"),
                name='pre_crop_z_T1')

            data_preparation_pipe.connect(
                inputnode, ("indiv_params", parse_key, "pre_crop_z_T1"),
                pre_crop_z_T1, 'indiv_params')

            if "avg_reorient_pipe" in params.keys():
                data_preparation_pipe.connect(av_T1, 'outputnode.std_img',
                                              pre_crop_z_T1, 'in_file')

            else:
                data_preparation_pipe.connect(av_T1, 'avg_img',
                                              pre_crop_z_T1, 'in_file')

        print('default crop_aladin_T1 will be run')
        crop_aladin_T1 = NodeParams(reg.RegAladin(),
                                    params=parse_key(params, "crop_aladin_T1"),
                                    name='crop_aladin_T1')

        crop_aladin_T1.inputs.ref_file = params_template["template_head"]

        data_preparation_pipe.connect(
            inputnode, ("indiv_params", parse_key, "crop_aladin_T1"),
            crop_aladin_T1, 'indiv_params')

        if "pre_crop_z_T1" in params.keys():
            data_preparation_pipe.connect(
                pre_crop_z_T1, "out_roi",
                crop_aladin_T1, 'flo_file')

        else:
            if "avg_reorient_pipe" in params.keys():
                data_preparation_pipe.connect(av_T1, 'outputnode.std_img',
                                              crop_aladin_T1, 'flo_file')
            else:
                data_preparation_pipe.connect(av_T1, 'avg_img',
                                              crop_aladin_T1, 'flo_file')

        # compute inv transfo
        inv_tranfo = NodeParams(
            regutils.RegTransform(),
            params=parse_key(params, "inv_transfo_aladin"),
            name='inv_tranfo')

        data_preparation_pipe.connect(crop_aladin_T1, 'aff_file',
                                      inv_tranfo, 'inv_aff_input')

        # crop_z_T1
        if "crop_z_T1" in params.keys():

            crop_z_T1 = NodeParams(fsl.RobustFOV(),
                                   params=parse_key(params, "crop_z_T1"),
                                   name='crop_z_T1')

            data_preparation_pipe.connect(crop_aladin_T1, "res_file",
                                          crop_z_T1, 'in_file')

            data_preparation_pipe.connect(
                inputnode, ("indiv_params", parse_key, "crop_z_T1"),
                crop_z_T1, 'indiv_params')

    # outputnode
    if "avg_reorient_pipe" in params.keys():
        data_preparation_pipe.connect(
            av_T1, 'outputnode.std_img',
            outputnode, 'native_T1')

    else:
        data_preparation_pipe.connect(av_T1, 'avg_img',
                                      outputnode, 'native_T1')

    if "denoise" in params.keys():

        # denoise with Ants package
        denoise_T1 = NodeParams(interface=DenoiseImage(),
                                params=parse_key(params, "denoise"),
                                name="denoise_T1")

        # inputs
        if "crop_T1" in params.keys():
            data_preparation_pipe.connect(crop_T1, "roi_file",
                                          denoise_T1, 'input_image')

        elif "crop_z_T1" in params.keys():
            data_preparation_pipe.connect(crop_z_T1, "out_roi",
                                          denoise_T1, 'input_image')

        else:
            data_preparation_pipe.connect(crop_aladin_T1, "res_file",
                                          denoise_T1, 'input_image')

        # outputs
        data_preparation_pipe.connect(denoise_T1, 'output_image',
                                      outputnode, 'preproc_T1')

    else:

        if "crop_T1" in params.keys():
            data_preparation_pipe.connect(crop_T1, "roi_file",
                                          outputnode, 'preproc_T1')

        elif "crop_z_T1" in params.keys():
            data_preparation_pipe.connect(crop_z_T1, "out_roi",
                                          outputnode, 'preproc_T1')

        else:
            data_preparation_pipe.connect(crop_aladin_T1, "res_file",
                                          outputnode, 'preproc_T1')

    return data_preparation_pipe
