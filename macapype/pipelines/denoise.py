import os
import shutil

import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni
import nipype.interfaces.ants as ants

from nipype.utils.filemanip import split_filename as split_f

from ..nodes.denoise import nonlocal_denoise

######################### Preprocessing: Avg multiples images, align T2 to T1, and crop/denoise in both order

def create_denoised_pipe(name="denoised_pipe"):

    # creating pipeline
    denoised_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['preproc_T1', 'preproc_T2']),
        name='inputnode')

    ## denoise aonlm

    denoise_T1 = pe.Node(
        niu.Function(input_names=["img_file"],
                     output_names=["denoised_img_file"],
                     function=nonlocal_denoise),
        name="denoise_T1")
    denoised_pipe.connect(inputnode, 'preproc_T1',
                                  denoise_T1, 'img_file')

    denoise_T2 = pe.Node(
        niu.Function(input_names=["img_file"],
                     output_names=["denoised_img_file"],
                     function =nonlocal_denoise),
        name="denoise_T2")
    denoised_pipe.connect(inputnode, 'preproc_T2',
                                  denoise_T2, 'img_file')

    return denoised_pipe
