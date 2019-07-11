
import os
import shutil

import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni
import nipype.interfaces.ants as ants

from nipype.utils.misc import show_files
from nipype.utils.filemanip import split_filename as split_f

#fsl.FSLCommand.set_default_output_type('NIFTI')

from ..nodes.segment import (
    average_align, nonlocal_denoise, average_align, nonlocal_denoise,
    print_val, print_nii_data,  wrap_NMT_subject_align, wrap_antsAtroposN4,
    add_Nwarp)

######################### Preprocessing: Avg multiples images, align T2 to T1, and crop/denoise in both order

def create_cropped_denoised_pipe(name= "cropped_denoised_pipe", crop_list = [(88, 144), (14, 180), (27, 103)], sigma = 4):

    # creating pipeline
    cropped_denoise_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1','T2']),
        name='inputnode')

    av_T1 = pe.Node(niu.Function(input_names = ['list_img'], output_names = ['avg_img'], function = average_align), name = "av_T1")
    cropped_denoised_pipe.connect(inputnode,'T1',av_T1,'list_img')

    av_T2 = pe.Node(niu.Function(input_names = ['list_img'], output_names = ['avg_img'], function = average_align), name = "av_T2")
    cropped_denoised_pipe.connect(inputnode,'T2',av_T2,'list_img')

    ### align avg T2 on avg T1
    align_T2_on_T1 = pe.Node(fsl.FLIRT(), name = "align_T2_on_T1")
    cropped_denoised_pipe.connect(av_T1,'avg_img',align_T2_on_T1,'reference')
    cropped_denoised_pipe.connect(av_T2,'avg_img',align_T2_on_T1,'in_file')
    align_T2_on_T1.inputs.dof = 6

    ######### cropping
    # Crop bounding box for T1
    crop_bb_T1 = pe.Node(fsl.ExtractROI(), name = 'crop_bb_T1')
    crop_bb_T1.inputs.crop_list = crop_list

    cropped_denoised_pipe.connect(av_T1,'avg_img',crop_bb_T1,'in_file')

    # Crop bounding box for T2
    crop_bb_T2 = pe.Node(fsl.ExtractROI(), name = 'crop_bb_T2')
    crop_bb_T2.inputs.crop_list = crop_list

    cropped_denoised_pipe.connect(align_T2_on_T1,'out_file',crop_bb_T2,'in_file')

    ########## denoise aonlm
    denoise_T1 = pe.Node(
        niu.Function(input_names = ["img_file"], output_names = ["denoised_img_file"], function = nonlocal_denoise),
        name = "denoise_T1")

    cropped_denoised_pipe.connect(crop_bb_T1,'roi_file',denoise_T1,'img_file')

    denoise_T2 = pe.Node(niu.Function(input_names = ["img_file"], output_names = ["denoised_img_file"], function = nonlocal_denoise), name = "denoise_T2")
    cropped_denoised_pipe.connect(crop_bb_T2,'roi_file',denoise_T2,'img_file')

    return cropped_denoised_pipe

def create_denoised_cropped_pipe(name= "denoised_cropped_pipe", crop_list = [(88, 144), (14, 180), (27, 103)], sigma = 4):

    # creating pipeline
    denoised_cropped_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1','T2']),
        name='inputnode')

    av_T1 = pe.Node(niu.Function(input_names = ['list_img'], output_names = ['avg_img'], function = average_align), name = "av_T1")
    denoised_cropped_pipe.connect(inputnode,'T1',av_T1,'list_img')

    av_T2 = pe.Node(niu.Function(input_names = ['list_img'], output_names = ['avg_img'], function = average_align), name = "av_T2")
    denoised_cropped_pipe.connect(inputnode,'T2',av_T2,'list_img')

    ### align avg T2 on avg T1
    align_T2_on_T1 = pe.Node(fsl.FLIRT(), name = "align_T2_on_T1")
    denoised_cropped_pipe.connect(av_T1,'avg_img',align_T2_on_T1,'reference')
    denoised_cropped_pipe.connect(av_T2,'avg_img',align_T2_on_T1,'in_file')
    align_T2_on_T1.inputs.dof = 6

    ########## denoise aonlm

    denoise_T1 = pe.Node(
        niu.Function(input_names = ["img_file"], output_names = ["denoised_img_file"], function = nonlocal_denoise),
        name = "denoise_T1")
    denoised_cropped_pipe.connect(av_T1,'avg_img',denoise_T1,'img_file')

    denoise_T2 = pe.Node(
        niu.Function(input_names = ["img_file"], output_names = ["denoised_img_file"], function = nonlocal_denoise),
        name = "denoise_T2")
    denoised_cropped_pipe.connect(align_T2_on_T1,'out_file',denoise_T2,'img_file')

    ######### cropping
    # Crop bounding box for T1
    crop_bb_T1 = pe.Node(fsl.ExtractROI(), name = 'crop_bb_T1')
    crop_bb_T1.inputs.crop_list = crop_list

    denoised_cropped_pipe.connect(denoise_T1,"denoised_img_file",crop_bb_T1,'in_file')

    # Crop bounding box for T2
    crop_bb_T2 = pe.Node(fsl.ExtractROI(), name = 'crop_bb_T2')
    crop_bb_T2.inputs.crop_list = crop_list

    denoised_cropped_pipe.connect(denoise_T2,"denoised_img_file",crop_bb_T2,'in_file')

    return denoised_cropped_pipe

############################################ correcting bias
def create_correct_bias_pipe(name= "correct_bias_pipe", sigma = 4):


    # creating pipeline
    correct_bias_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['preproc_T1','preproc_T2']),
        name='inputnode')

    #### BinaryMaths
    mult_T1_T2 = pe.Node(fsl.BinaryMaths(),name = 'mult_T1_T2')
    mult_T1_T2.inputs.operation = "mul"
    mult_T1_T2.inputs.args = "-abs -sqrt"
    mult_T1_T2.inputs.output_datatype = "float"

    correct_bias_pipe.connect(inputnode,'preproc_T1',mult_T1_T2,'in_file')
    correct_bias_pipe.connect(inputnode,'preproc_T2',mult_T1_T2,'operand_file')

    ## Mean Brain Val
    meanbrainval = pe.Node(fsl.ImageStats(),name ='meanbrainval')
    meanbrainval.inputs.op_string = "-M"

    correct_bias_pipe.connect(mult_T1_T2,'out_file',meanbrainval,'in_file')

    ### norm_mult
    norm_mult= pe.Node(fsl.BinaryMaths(),name = 'norm_mult')
    norm_mult.inputs.operation = "div"

    correct_bias_pipe.connect(mult_T1_T2,'out_file',norm_mult,'in_file')
    correct_bias_pipe.connect(meanbrainval,('out_stat',print_val),norm_mult,'operand_value')

    ### smooth
    smooth= pe.Node(fsl.maths.MathsCommand(),name = 'smooth')
    smooth.inputs.args = "-bin -s {}".format(sigma)

    correct_bias_pipe.connect(norm_mult,'out_file',smooth,'in_file')

    ### norm_smooth
    norm_smooth= pe.Node(fsl.MultiImageMaths(),name = 'norm_smooth')
    norm_smooth.inputs.op_string = "-s {} -div %s".format(sigma)

    correct_bias_pipe.connect(norm_mult,'out_file',norm_smooth,'in_file')
    correct_bias_pipe.connect(smooth,'out_file',norm_smooth,'operand_files')
    #correct_bias_pipe.connect(smooth,('out_file',print_nii_data),norm_smooth,'operand_files')

    #norm_smooth= pe.Node(fsl.IsotropicSmooth(),name = 'norm_smooth')
    #norm_smooth.inputs.sigma = sigma
    #correct_bias_pipe.connect(norm_mult,'out_file',norm_smooth,'in_file')

    ### modulate
    modulate= pe.Node(fsl.BinaryMaths(),name = 'modulate')
    modulate.inputs.operation = "div"

    correct_bias_pipe.connect(norm_mult,'out_file',modulate,'in_file')
    correct_bias_pipe.connect(norm_smooth,'out_file',modulate,'operand_file')
    #correct_bias_pipe.connect(norm_smooth,('out_file',print_nii_data),modulate,'operand_file')

    ### std_modulate
    std_modulate = pe.Node(fsl.ImageStats(),name ='std_modulate')
    std_modulate.inputs.op_string = "-S"

    #correct_bias_pipe.connect(modulate,'out_file',std_modulate,'in_file')
    correct_bias_pipe.connect(modulate,('out_file',print_nii_data),std_modulate,'in_file')

    ### mean_modulate
    mean_modulate = pe.Node(fsl.ImageStats(),name ='mean_modulate')
    mean_modulate.inputs.op_string = "-M"

    correct_bias_pipe.connect(modulate,'out_file',mean_modulate,'in_file')


    ######################################## Mask
    def compute_lower_val(mean_val,std_val):

        return mean_val - (std_val*0.5)


    ### compute_lower
    lower = pe.Node(niu.Function(input_names = ['mean_val','std_val'], output_names = ['lower_val'], function = compute_lower_val), name = 'lower')

    correct_bias_pipe.connect(mean_modulate,'out_stat',lower,'mean_val')
    correct_bias_pipe.connect(std_modulate,'out_stat',lower,'std_val')

    ### thresh_lower
    thresh_lower = pe.Node(fsl.Threshold(),name ='thresh_lower')


    correct_bias_pipe.connect(lower,'lower_val',thresh_lower,'thresh')
    correct_bias_pipe.connect(modulate,'out_file',thresh_lower,'in_file')


    ### mod_mask

    mod_mask = pe.Node(fsl.UnaryMaths(),name ='mod_mask')
    mod_mask.inputs.operation = "bin"
    mod_mask.inputs.args = "-ero -mul 255"

    #correct_bias_pipe.connect(correct_bias,'thresh_lower_file',mod_mask,'in_file') #OR
    correct_bias_pipe.connect(thresh_lower,'out_file',mod_mask,'in_file')


    ##tmp_bias
    tmp_bias = pe.Node(fsl.MultiImageMaths(),name ='tmp_bias')
    tmp_bias.inputs.op_string = "-mas %s"
    tmp_bias.inputs.output_datatype = "float"

    #correct_bias_pipe.connect(correct_bias,'norm_mult_file',bias,'in_file') #OR
    correct_bias_pipe.connect(norm_mult,'out_file',tmp_bias,'in_file')

    correct_bias_pipe.connect(mod_mask,'out_file',tmp_bias,'operand_files')

    ##bias
    bias = pe.Node(fsl.MultiImageMaths(),name ='bias')
    bias.inputs.op_string = "-mas %s -dilall"
    bias.inputs.output_datatype = "float"

    #correct_bias_pipe.connect(correct_bias,'norm_mult_file',bias,'in_file') #OR
    correct_bias_pipe.connect(norm_mult,'out_file',bias,'in_file')

    correct_bias_pipe.connect(mod_mask,'out_file',bias,'operand_files')

    ### smooth_bias
    smooth_bias= pe.Node(fsl.IsotropicSmooth(),name = 'smooth_bias')
    smooth_bias.inputs.sigma = sigma

    correct_bias_pipe.connect(bias,'out_file',smooth_bias,'in_file')

    ### restore_T1
    restore_T1 = pe.Node(fsl.BinaryMaths(),name = 'restore_T1')
    restore_T1.inputs.operation = "div"
    restore_T1.inputs.output_datatype = "float"

    correct_bias_pipe.connect(inputnode,'preproc_T1', restore_T1,'in_file')
    correct_bias_pipe.connect(smooth_bias,'out_file',restore_T1,'operand_file')

    ### restore_T2
    restore_T2 = pe.Node(fsl.BinaryMaths(),name = 'restore_T2')
    restore_T2.inputs.operation = "div"
    restore_T2.inputs.output_datatype = "float"

    correct_bias_pipe.connect(inputnode,'preproc_T2', restore_T2,'in_file')
    correct_bias_pipe.connect(smooth_bias,'out_file',restore_T2,'operand_file')

    return correct_bias_pipe

def create_brain_extraction_pipe(name = "brain_extraction_pipe"):

    # creating pipeline
    brain_extraction_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['restore_T1','restore_T2']),
        name='inputnode')

    def apply_atlasBREX(t1_restored_file):

        cur_dir = os.path.abspath("")
        print cur_dir

        script_dir = "/hpc/meca/users/loh.k/macaque_preprocessing/preproc_cloud/processing_scripts/"
        script_atlas_BREX = os.path.join(script_dir,"atlasBREX_fslfrioul.sh")
        shutil.copy(script_atlas_BREX,cur_dir)

        ### all files need to be copied in cur_dir
        nmt_dir="/hpc/meca/users/loh.k/macaque_preprocessing/NMT_v1.2/"
        nmt_file = os.path.join(nmt_dir,"NMT.nii.gz")
        shutil.copy(nmt_file,cur_dir)

        nmt_ss_file = os.path.join(nmt_dir,"NMT_SS.nii.gz")
        shutil.copy(nmt_ss_file,cur_dir)

        path, fname, ext = split_f(t1_restored_file)
        print(path, fname, ext)
        shutil.copy(t1_restored_file,cur_dir)


        ## just to be sure...
        os.chdir(cur_dir)

        if ext == ".nii":
            print("zipping {} as expected by atlas_brex".format(t1_restored_file))
            os.system("gzip {}".format(fname+ ext))
            ext = ".nii.gz"

        os.system("bash {} -b {} -nb {} -h {} -f 0.5 -reg 1 -w 10,10,10 -msk a,0,0".format("atlasBREX_fslfrioul.sh", "NMT_SS.nii.gz", "NMT.nii.gz", fname + ext))

        ##get mask filename
        brain_file=os.path.abspath(fname + "_brain" + ext)

        return brain_file

    ### atlas_brex
    atlas_brex = pe.Node(niu.Function(input_names = ['t1_restored_file'], output_names = ['brain_file'], function = apply_atlasBREX), name = 'atlas_brex')

    brain_extraction_pipe.connect(inputnode,"restore_T1",atlas_brex,'t1_restored_file')

    ### mask_brex
    mask_brex = pe.Node(fsl.UnaryMaths(),name = 'mask_brex')
    mask_brex.inputs.operation = 'bin'

    brain_extraction_pipe.connect(atlas_brex,'brain_file',mask_brex,'in_file')

    ### smooth_mask
    smooth_mask= pe.Node(fsl.UnaryMaths(),name = 'smooth_mask')
    smooth_mask.inputs.operation = "bin"
    smooth_mask.inputs.args = "-s 1 -thr 0.5 -bin"

    brain_extraction_pipe.connect(mask_brex,'out_file',smooth_mask,'in_file')

    ### mult_T1
    mult_T1= pe.Node(afni.Calc(),name = 'mult_T1')
    mult_T1.inputs.expr="a*b"
    mult_T1.inputs.outputtype='NIFTI_GZ'

    brain_extraction_pipe.connect(inputnode,"restore_T1",mult_T1,'in_file_a')
    brain_extraction_pipe.connect(smooth_mask,'out_file',mult_T1,'in_file_b')

    ### mult_T2
    mult_T2= pe.Node(afni.Calc(),name = 'mult_T2')
    mult_T2.inputs.expr="a*b"
    mult_T2.inputs.outputtype='NIFTI_GZ'

    brain_extraction_pipe.connect(inputnode,'restore_T1',mult_T2,'in_file_a')
    brain_extraction_pipe.connect(smooth_mask,'out_file',mult_T2,'in_file_b')

    return brain_extraction_pipe


def create_brain_segment_pipe(name = "brain_segment_pipe"):

    # creating pipeline
    brain_segment_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['extracted_T1']),
        name='inputnode')

    ########################### align subj to nmt


    ### NMT_subject_align
    NMT_subject_align= pe.Node(niu.Function(input_names = ["T1_file"], output_names = ["shft_aff_file", "warpinv_file", "transfo_file", "inv_transfo_file"], function = wrap_NMT_subject_align),name = 'NMT_subject_align')

    brain_segment_pipe.connect(inputnode,'extracted_T1',NMT_subject_align,"T1_file")

    ######################################### segmentation

    ### # STEP1 : align_masks

    nmt_dir="/hpc/meca/users/loh.k/macaque_preprocessing/NMT_v1.2/"

    NMT_file = os.path.join(nmt_dir,"NMT.nii.gz")
    NMT_brainmask_prob = os.path.join(nmt_dir,"masks","probabilisitic_segmentation_masks","NMT_brainmask_prob.nii.gz")
    NMT_brainmask = os.path.join(nmt_dir,"masks","anatomical_masks","NMT_brainmask.nii.gz")
    NMT_brainmask_CSF = os.path.join(nmt_dir,"masks","probabilisitic_segmentation_masks","NMT_segmentation_CSF.nii.gz")
    NMT_brainmask_GM = os.path.join(nmt_dir,"masks","probabilisitic_segmentation_masks","NMT_segmentation_GM.nii.gz")
    NMT_brainmask_WM = os.path.join(nmt_dir,"masks","probabilisitic_segmentation_masks","NMT_segmentation_WM.nii.gz")

    list_priors = [NMT_file, NMT_brainmask_prob, NMT_brainmask, NMT_brainmask_CSF, NMT_brainmask_GM, NMT_brainmask_WM]
    align_masks = pe.Node(afni.NwarpApply(),name = 'align_masks')
    align_masks.inputs.in_file= list_priors
    align_masks.inputs.out_file= add_Nwarp(list_priors)
    align_masks.inputs.interp="NN"
    align_masks.inputs.args="-overwrite"

    brain_segment_pipe.connect(NMT_subject_align,'shft_aff_file',align_masks,'master')
    brain_segment_pipe.connect(NMT_subject_align,'warpinv_file',align_masks,"warp")

    # STEP2: N4 intensity normalization over brain
    norm_intensity = pe.Node(ants.N4BiasFieldCorrection(),name = 'norm_intensity')
    norm_intensity.inputs.dimension = 3

    brain_segment_pipe.connect(NMT_subject_align,'shft_aff_file',norm_intensity,"input_image")

    ### #STEP 3: ants Atropos

    #make brainmask from brain image

    ### make_brainmask
    make_brainmask = pe.Node(fsl.Threshold(),name = 'make_brainmask')
    make_brainmask.inputs.thresh = 1
    make_brainmask.inputs.args = '-bin'

    brain_segment_pipe.connect(norm_intensity,'output_image',make_brainmask,'in_file')

    # Atropos
    seg_at = pe.Node(niu.Function(
        input_names = ["dimension","shft_aff_file", "brainmask_file","numberOfClasses","ex_prior"],
        output_names = ["out_files","seg_file","seg_post1_file","seg_post2_file", "seg_post3_file"],
        function = wrap_antsAtroposN4), name = 'seg_at')

    seg_at.inputs.dimension = 3
    seg_at.inputs.numberOfClasses = 3

    brain_segment_pipe.connect(NMT_subject_align,'shft_aff_file',seg_at,"shft_aff_file")
    brain_segment_pipe.connect(make_brainmask,'out_file',seg_at,"brainmask_file")
    brain_segment_pipe.connect(align_masks,('out_file',show_files),seg_at,"ex_prior")

    ### align result file to subj
    # first for brainmask
    align_brainmask = pe.Node(afni.Allineate(), name = "align_brainmask")
    align_brainmask.inputs.final_interpolation = "nearestneighbour"
    align_brainmask.inputs.overwrite = True
    align_brainmask.inputs.outputtype = "NIFTI_GZ"

    brain_segment_pipe.connect(make_brainmask,'out_file',align_brainmask,"in_file") # -source
    brain_segment_pipe.connect(inputnode,'extracted_T1',align_brainmask,"reference") # -base
    brain_segment_pipe.connect(NMT_subject_align,'inv_transfo_file',align_brainmask,"in_matrix") # -1Dmatrix_apply

    ## looping over the Segmentation files with MapNode
    # probleme avec la liste???? avec l'encodage unicode u''????

    #align_all_seg = pe.MapNode(interface = afni.Allineate(), iterfield = ["in_file"], name = "align_all_seg")
    #align_all_seg.inputs.final_interpolation = "nearestneighbour"
    #align_all_seg.inputs.overwrite = True
    #align_all_seg.inputs.outputtype = "NIFTI_GZ"

    #seg_pipe.connect(seg_at,('out_files',show_files),align_all_seg,"in_file") # -source
    #seg_pipe.connect(mult_T1,'out_file',align_all_seg,"reference") # -base
    #seg_pipe.connect(NMT_subject_align,'inv_transfo_file',align_all_seg,"in_matrix") # -1Dmatrix_apply

    ### align segmentation one by one:
    #seg
    align_seg = pe.Node(afni.Allineate(),  name = "align_seg")
    align_seg.inputs.final_interpolation = "nearestneighbour"
    align_seg.inputs.overwrite = True
    align_seg.inputs.outputtype = "NIFTI_GZ"

    brain_segment_pipe.connect(seg_at,("seg_file",show_files),align_seg,"in_file") # -source
    brain_segment_pipe.connect(inputnode,'extracted_T1',align_seg,"reference") # -base
    brain_segment_pipe.connect(NMT_subject_align,'inv_transfo_file',align_seg,"in_matrix") # -1Dmatrix_apply

    #seg_post1
    align_seg_post1 = pe.Node(afni.Allineate(),  name = "align_seg_post1")
    align_seg_post1.inputs.final_interpolation = "nearestneighbour"
    align_seg_post1.inputs.overwrite = True
    align_seg_post1.inputs.outputtype = "NIFTI_GZ"

    brain_segment_pipe.connect(seg_at,"seg_post1_file",align_seg_post1,"in_file") # -source
    brain_segment_pipe.connect(inputnode,'extracted_T1',align_seg_post1,"reference") # -base
    brain_segment_pipe.connect(NMT_subject_align,'inv_transfo_file',align_seg_post1,"in_matrix") # -1Dmatrix_apply

    #seg_post2
    align_seg_post2 = pe.Node(afni.Allineate(),  name = "align_seg_post2")
    align_seg_post2.inputs.final_interpolation = "nearestneighbour"
    align_seg_post2.inputs.overwrite = True
    align_seg_post2.inputs.outputtype = "NIFTI_GZ"

    brain_segment_pipe.connect(seg_at,"seg_post2_file",align_seg_post2,"in_file") # -source
    brain_segment_pipe.connect(inputnode,'extracted_T1',align_seg_post2,"reference") # -base
    brain_segment_pipe.connect(NMT_subject_align,'inv_transfo_file',align_seg_post2,"in_matrix") # -1Dmatrix_apply

    #seg_post3
    align_seg_post3 = pe.Node(afni.Allineate(),  name = "align_seg_post3")
    align_seg_post3.inputs.final_interpolation = "nearestneighbour"
    align_seg_post3.inputs.overwrite = True
    align_seg_post3.inputs.outputtype = "NIFTI_GZ"

    brain_segment_pipe.connect(seg_at,"seg_post3_file",align_seg_post3,"in_file") # -source
    brain_segment_pipe.connect(inputnode,'extracted_T1',align_seg_post3,"reference") # -base
    brain_segment_pipe.connect(NMT_subject_align,'inv_transfo_file',align_seg_post3,"in_matrix") # -1Dmatrix_apply

    return brain_segment_pipe
