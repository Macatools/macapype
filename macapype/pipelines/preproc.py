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

################## on the fly
def read_cropbox(cropbox_file):

    import os.path as op

    assert op.exists(cropbox_file), \
        "Error {} do not exists".format(cropbox_file)

    with open(cropbox_file) as f:
        crop_list = []
        for line in f.readlines():
            print (line.strip().split())
            crop_list.append( tuple(map(int,map(float, line.strip().split()))))

    print(crop_list )
    return crop_list

def create_average_align_cropped_pipe(name = 'average_align_pipe'):
    """
    preprocessing:
    - av = checking if multiples T1 and T2 and if it is the case,
    coregister and average (~ flirt_average)
    - coregister T2 on T1 with FLIRT
    """

    # creating pipeline
    preproc_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1', 'T2', 'T1cropbox', 'T2cropbox']),
        name='inputnode')

    av_T1 = pe.Node(niu.Function(input_names = ['list_img'], output_names = ['avg_img'], function = average_align), name = "av_T1")
    preproc_pipe.connect(inputnode,'T1',av_T1,'list_img')

    av_T2 = pe.Node(niu.Function(input_names = ['list_img'], output_names = ['avg_img'], function = average_align), name = "av_T2")
    preproc_pipe.connect(inputnode, 'T2', av_T2, 'list_img')

    ### align avg T2 on avg T1
    align_T2_on_T1 = pe.Node(fsl.FLIRT(), name = "align_T2_on_T1")
    preproc_pipe.connect(av_T1, 'avg_img', align_T2_on_T1, 'reference')
    preproc_pipe.connect(av_T2, 'avg_img', align_T2_on_T1, 'in_file')
    align_T2_on_T1.inputs.dof = 6


    # cropping
    # Crop bounding box for T1
    crop_bb_T1 = pe.Node(fsl.ExtractROI(), name='crop_bb_T1')


    preproc_pipe.connect(inputnode, ("T1cropbox",read_cropbox),
                                  crop_bb_T1, 'crop_list')

    preproc_pipe.connect(av_T1, "avg_img",
                                  crop_bb_T1, 'in_file')

    # Crop bounding box for T2
    crop_bb_T2 = pe.Node(fsl.ExtractROI(), name='crop_bb_T2')

    preproc_pipe.connect(inputnode, ("T2cropbox",read_cropbox),
                                  crop_bb_T2, 'crop_list')

    preproc_pipe.connect(align_T2_on_T1, "out_file",
                                  crop_bb_T2, 'in_file')

    return preproc_pipe

def create_average_align_pipe(name = 'average_align_pipe'):
    """
    preprocessing:
    - av = checking if multiples T1 and T2 and if it is the case,
    coregister and average (~ flirt_average)
    - coregister T2 on T1 with FLIRT
    """

    # creating pipeline
    preproc_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1', 'T2']),
        name='inputnode')

    av_T1 = pe.Node(
        niu.Function(input_names = ['list_img'],
                     output_names = ['avg_img'],
                     function = average_align),
        name = "av_T1")

    preproc_pipe.connect(inputnode,'T1',av_T1,'list_img')

    av_T2 = pe.Node(niu.Function(
        input_names = ['list_img'],
        output_names = ['avg_img'],
        function = average_align), name = "av_T2")

    preproc_pipe.connect(inputnode, 'T2', av_T2, 'list_img')

    ### align avg T2 on avg T1
    align_T2_on_T1 = pe.Node(fsl.FLIRT(), name = "align_T2_on_T1")
    preproc_pipe.connect(av_T1, 'avg_img', align_T2_on_T1, 'reference')
    preproc_pipe.connect(av_T2, 'avg_img', align_T2_on_T1, 'in_file')
    align_T2_on_T1.inputs.dof = 6

    return preproc_pipe

