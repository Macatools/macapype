
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.ants as ants

from ..utils.utils_nodes import NodeParams

from nipype.interfaces.ants.segmentation import DenoiseImage

# from nipype.interfaces.freesurfer.prepareess import MRIConvert

from ..nodes.prepare import average_align, FslOrient, read_cropbox

from ..nodes.extract_brain import T1xT2BET

from macapype.utils.misc import get_first_elem


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
        niu.IdentityInterface(fields=['T1', 'T2']),
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

    return data_preparation_pipe


##BABOON TEST###

def create_data_preparation_baboon_pipe(params, name="data_preparation_baboon_pipe"):
    """
    prepare:
    - reorient if needed (makes the whole pipeline more neat)
    - start by denoising all input images -> so we dont have to keep repeating it if we are testing other parameters in dataprep (e.g. cropping)
    - crop T1 and T2 based on individual parameters
    - running N4biascorrection on cropped T1 and T2 -> to help T2 and T1 alignment
    - align T2 to T1
    """

    # creating pipeline
    data_preparation_baboon_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1', 'T2']),
        name='inputnode'
    )
    
    #reorient if needed
    if "reorient" in params.keys():

        if "new_dims" in params["reorient"].keys():
            new_dims = tuple(params["reorient"]["new_dims"].split())

        else:
            new_dims = ("x", "z", "-y")

            reorient_T1_pipe = create_reorient_pipeline(name="reorient_T1_pipe",new_dims=new_dims)
            data_preparation_baboon_pipe.connect(inputnode, ('T1',get_first_elem), reorient_T1_pipe, 'inputnode.image')

            reorient_T2_pipe = create_reorient_pipeline(name="reorient_T2_pipe", new_dims=new_dims)
            data_preparation_baboon_pipe.connect(inputnode, ('T2',get_first_elem), reorient_T2_pipe, 'inputnode.image')
   
    # denoise with Ants package (taking into account whether reorient has been performed or not)
    denoise_T1 = pe.Node(interface=DenoiseImage(), name="denoise_T1")
    denoise_T2 = pe.Node(interface=DenoiseImage(), name="denoise_T2")

    if "reorient" in params.keys():

        data_preparation_baboon_pipe.connect(reorient_T1_pipe,
                                          'swap_dim.out_file',
                                          denoise_T1, 'input_image')
        data_preparation_baboon_pipe.connect(reorient_T2_pipe,
                                          'swap_dim.out_file',
                                          denoise_T2, 'input_image')
    else:
        data_preparation_baboon_pipe.connect(inputnode, ('T1',get_first_elem),
                                          denoise_T1, 'input_image')
        data_preparation_baboon_pipe.connect(inputnode, ('T2',get_first_elem),
                                          denoise_T2, 'input_image')
   
    #cropping

    if "bet_crop" in params.keys():

        print('bet_crop is in params')

        # Brain extraction (unused) + Cropping
        bet_crop = NodeParams(T1xT2BET(), params=params["bet_crop"],
                              name='bet_crop')

        data_preparation_baboon_pipe.connect(denoise_T1,'output_image',bet_crop, 't1_file')
        data_preparation_baboon_pipe.connect(denoise_T2,'output_image',bet_crop, 't2_file')

    elif "crop" in params.keys():
        print('crop is in params')

        assert "croplist_T1" in params["crop"].keys(), \
            "Error, T1 croplist is not specified for crop node, breaking"

        assert "croplist_T2" in params["crop"].keys(), \
            "Error, T2 croplist is not specified for crop node, breaking"

        # cropping
        # Crop bounding box for T1
        crop_bb_T1 = pe.Node(fsl.ExtractROI(), name='crop_bb_T1')
        crop_bb_T1.inputs.args = params["crop"]["croplist_T1"]

        # Crop bounding box for T2
        crop_bb_T2 = pe.Node(fsl.ExtractROI(), name='crop_bb_T2')
        crop_bb_T2.inputs.args = params["crop"]["croplist_T2"]

        data_preparation_baboon_pipe.connect(denoise_T1,'output_image', crop_bb_T1, 'in_file')
        data_preparation_baboon_pipe.connect(denoise_T2,'output_image', crop_bb_T2, 'in_file')

    # N4 intensity normalization with parameters from json
    norm_intensity_T1 = NodeParams(ants.N4BiasFieldCorrection(),name='norm_intensity_T1')
    norm_intensity_T2 = NodeParams(ants.N4BiasFieldCorrection(),name='norm_intensity_T2')

    if "norm_intensity" in params.keys():
        norm_intensity_T1.load_inputs_from_dict(params["norm_intensity"])
        norm_intensity_T2.load_inputs_from_dict(params["norm_intensity"])

    data_preparation_baboon_pipe.connect(crop_bb_T1, 'roi_file', norm_intensity_T1, "input_image")
    data_preparation_baboon_pipe.connect(crop_bb_T2, 'roi_file', norm_intensity_T2, "input_image")

    # align T2 on T1 - mutualinfo works better for crossmodal registration for images with bias

    align_T2_on_T1 = pe.Node(fsl.FLIRT(), name="align_T2_on_T1")
    align_T2_on_T1.inputs.dof = 6
    align_T2_on_T1.inputs.cost = 'normmi'

    data_preparation_baboon_pipe.connect(norm_intensity_T1,'output_image',align_T2_on_T1, 'reference')
    data_preparation_baboon_pipe.connect(norm_intensity_T2,'output_image',align_T2_on_T1, 'in_file')

    return data_preparation_baboon_pipe



###############################################################################
# Old version of align_crop

def create_average_align_crop_pipe(name='average_align_pipe'):
    """
    prepare:
    - av = checking if multiples T1 and T2 and if it is the case,
    coregister and average (~ flirt_average)
    - coregister T2 on T1 with FLIRT
    - crop using .cropbox file
    """

    # creating pipeline
    data_preparation_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1', 'T2', 'T1cropbox', 'T2cropbox']),
        name='inputnode')

    av_T1 = pe.Node(niu.Function(input_names=['list_img'],
                                 output_names=['avg_img'],
                                 function=average_align), name="av_T1")

    data_preparation_pipe.connect(inputnode, 'T1', av_T1, 'list_img')

    av_T2 = pe.Node(niu.Function(input_names=['list_img'],
                                 output_names=['avg_img'],
                                 function=average_align), name="av_T2")

    data_preparation_pipe.connect(inputnode, 'T2', av_T2, 'list_img')

    # align avg T2 on avg T1
    align_T2_on_T1 = pe.Node(fsl.FLIRT(), name="align_T2_on_T1")
    data_preparation_pipe.connect(av_T1, 'avg_img',
                                  align_T2_on_T1, 'reference')
    data_preparation_pipe.connect(av_T2, 'avg_img', align_T2_on_T1, 'in_file')
    align_T2_on_T1.inputs.dof = 6

    # cropping
    # Crop bounding box for T1
    crop_bb_T1 = pe.Node(fsl.ExtractROI(), name='crop_bb_T1')

    data_preparation_pipe.connect(inputnode, ("T1cropbox", read_cropbox),
                                  crop_bb_T1, 'crop_list')

    data_preparation_pipe.connect(av_T1, "avg_img", crop_bb_T1, 'in_file')

    # Crop bounding box for T2
    crop_bb_T2 = pe.Node(fsl.ExtractROI(), name='crop_bb_T2')

    data_preparation_pipe.connect(inputnode, ("T2cropbox", read_cropbox),
                                  crop_bb_T2, 'crop_list')

    data_preparation_pipe.connect(align_T2_on_T1, "out_file",
                                  crop_bb_T2, 'in_file')

    return data_preparation_pipe


def create_average_align_pipe(name='average_align_pipe'):
    """
    prepareessing:
    - av = checking if multiples T1 and T2 and if it is the case,
    coregister and average (~ flirt_average)
    - coregister T2 on T1 with FLIRT
    """

    # creating pipeline
    data_preparation_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1', 'T2']),
        name='inputnode')

    av_T1 = pe.Node(
        niu.Function(input_names=['list_img'],
                     output_names=['avg_img'],
                     function=average_align),
        name="av_T1")

    data_preparation_pipe.connect(inputnode, 'T1', av_T1, 'list_img')

    av_T2 = pe.Node(niu.Function(
        input_names=['list_img'],
        output_names=['avg_img'],
        function=average_align), name="av_T2")

    data_preparation_pipe.connect(inputnode, 'T2', av_T2, 'list_img')

    # align avg T2 on avg T1
    align_T2_on_T1 = pe.Node(fsl.FLIRT(), name="align_T2_on_T1")
    data_preparation_pipe.connect(av_T1, 'avg_img',
                                  align_T2_on_T1, 'reference')
    data_preparation_pipe.connect(av_T2, 'avg_img', align_T2_on_T1, 'in_file')
    align_T2_on_T1.inputs.dof = 6

    return data_preparation_pipe
