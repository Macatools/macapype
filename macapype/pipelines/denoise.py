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

from ..nodes.denoise import nonlocal_denoise

######################### Preprocessing: Avg multiples images, align T2 to T1, and crop/denoise in both order
def create_cropped_denoised_pipe(name= "cropped_denoised_pipe", crop_list = [(88, 144), (14, 180), (27, 103)], sigma = 4):

    # creating pipeline
    cropped_denoised_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['preproc_T1','preproc_T2']),
        name='inputnode')

    ######### cropping
    # Crop bounding box for T1
    crop_bb_T1 = pe.Node(fsl.ExtractROI(), name = 'crop_bb_T1')
    crop_bb_T1.inputs.crop_list = crop_list

    cropped_denoised_pipe.connect(inputnode,'preproc_T1',crop_bb_T1,'in_file')

    # Crop bounding box for T2
    crop_bb_T2 = pe.Node(fsl.ExtractROI(), name = 'crop_bb_T2')
    crop_bb_T2.inputs.crop_list = crop_list

    cropped_denoised_pipe.connect(inputnode,'preproc_T2',crop_bb_T2,'in_file')

    ########## denoise aonlm
    denoise_T1 = pe.Node(
        niu.Function(input_names =["img_file"],
                     output_names=["denoised_img_file"],
                     function = nonlocal_denoise),
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
        niu.IdentityInterface(fields=['preproc_T1','preproc_T2']),
        name='inputnode')

    ########## denoise aonlm

    denoise_T1 = pe.Node(
        niu.Function(input_names = ["img_file"], output_names = ["denoised_img_file"], function = nonlocal_denoise),
        name = "denoise_T1")
    denoised_cropped_pipe.connect(inputnode,'preproc_T1',denoise_T1,'img_file')

    denoise_T2 = pe.Node(
        niu.Function(input_names = ["img_file"], output_names = ["denoised_img_file"], function = nonlocal_denoise),
        name = "denoise_T2")
    denoised_cropped_pipe.connect(inputnode,'preproc_T2',denoise_T2,'img_file')

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
