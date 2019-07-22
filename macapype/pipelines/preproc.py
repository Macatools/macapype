import os
import shutil

import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni
import nipype.interfaces.ants as ants

from nipype.utils.filemanip import split_filename as split_f

from ..nodes.preproc import average_align

def create_average_align_pipe(name = 'average_align_pipe'):
    """
    preprocessing:
    - av = checking if multiples T1 and T2 and if it is the case,
    coregister and average (~ flirt_average)
    - coregister T2 on T1 with FLIRT
    """

    # creating pipeline
    average_align_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1','T2']),
        name='inputnode')

    av_T1 = pe.Node(niu.Function(input_names = ['list_img'], output_names = ['avg_img'], function = average_align), name = "av_T1")
    average_align_pipe.connect(inputnode,'T1',av_T1,'list_img')

    av_T2 = pe.Node(niu.Function(input_names = ['list_img'], output_names = ['avg_img'], function = average_align), name = "av_T2")
    average_align_pipe.connect(inputnode,'T2',av_T2,'list_img')

    ### align avg T2 on avg T1
    align_T2_on_T1 = pe.Node(fsl.FLIRT(), name = "align_T2_on_T1")
    average_align_pipe.connect(av_T1,'avg_img',align_T2_on_T1,'reference')
    average_align_pipe.connect(av_T2,'avg_img',align_T2_on_T1,'in_file')
    align_T2_on_T1.inputs.dof = 6

    return average_align_pipe
