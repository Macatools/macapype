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

from ..nodes.segment import average_align

from ..nodes.denoise import nonlocal_denoise

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

def create_denoised_cropped_pipe(name="denoised_cropped_pipe",
                                 crop_list=[(88, 144), (14, 180), (27, 103)],
                                 sigma=4):

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
