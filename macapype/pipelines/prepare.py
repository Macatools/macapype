
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl

from ..utils.utils_nodes import NodeParams, output_key_exists, parse_key

from nipype.interfaces.ants.segmentation import DenoiseImage

# from nipype.interfaces.freesurfer.prepareess import MRIConvert

from ..nodes.prepare import average_align, FslOrient, read_cropbox

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


def create_data_preparation_pipe(params, name="data_preparation_pipe"):
    """
    Description
    prepare:
    - av = checking if multiples T1 and T2 and if it is the case,
    coregister and average (~ flirt_average)
    - reorient (optional)
    - coregister T2 on T1 with FLIRT
    - crop using .cropbox file
    - denoising

    Inputs:

        inputnode:
            T1: T1 file name
            T2: T2 file name
            indiv_params (opt): dict with individuals parameters for some nodes

        arguments:
            params_template: dictionary of info about template

            params: dictionary of node sub-parameters (from a json file)

            name: pipeline name (default = "register_NMT_pipe")

    Outputs:

        denoise_T1.output_image:
            denoised T1
        denoise_T2.output_image:
            denoise T2
        bet_crop.mask_file(opt):
            mask from T1xT2BET

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

        reorient_T1_pipe = create_reorient_pipeline(name="reorient_T1_pipe",
                                                    new_dims=new_dims)
        data_preparation_pipe.connect(av_T1, 'avg_img',
                                      reorient_T1_pipe, 'inputnode.image')

        reorient_T2_pipe = create_reorient_pipeline(name="reorient_T2_pipe",
                                                    new_dims=new_dims)
        data_preparation_pipe.connect(av_T2, 'avg_img',
                                      reorient_T2_pipe, 'inputnode.image')

    # Align T2 -> T1 and crop (if specified)
    if output_key_exists(inputnode, 'indiv_params', "crop"):
        print('crop is in params')

        # align avg T2 on avg T1
        align_T2_on_T1 = pe.Node(fsl.FLIRT(), name="align_T2_on_T1")
        align_T2_on_T1.inputs.dof = 6

        # cropping
        # Crop bounding box for T1
        crop_bb_T1 = NodeParams(fsl.ExtractROI(), name='crop_bb_T1')

        data_preparation_pipe.connect(
            inputnode, ('indiv_params', parse_key, "crop"),
            crop_bb_T1, 'indiv_params')

        # Crop bounding box for T2
        crop_bb_T2 = NodeParams(fsl.ExtractROI(), name='crop_bb_T2')

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

    if output_key_exists(inputnode, 'indiv_params', "crop"):
        data_preparation_pipe.connect(crop_bb_T1, "roi_file",
                                      denoise_T1, 'input_image')
        data_preparation_pipe.connect(crop_bb_T2, "roi_file",
                                      denoise_T2, 'input_image')

    elif "bet_crop" in params.keys():
        data_preparation_pipe.connect(bet_crop, "t1_cropped_file",
                                      denoise_T1, 'input_image')
        data_preparation_pipe.connect(bet_crop, "t2_cropped_file",
                                      denoise_T2, 'input_image')

    else:
        data_preparation_pipe.connect(av_T1, 'avg_img',
                                      denoise_T1, 'input_image')

        data_preparation_pipe.connect(align_T2_on_T1, "out_file",
                                      denoise_T2, 'input_image')


    return data_preparation_pipe
