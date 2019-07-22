import nipype

import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from nipype.utils.misc import show_files

import nipype.interfaces.fsl as fsl
fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

import os

from macapype.pipelines.preproc import create_average_align_pipe
from macapype.pipelines.denoise import (
    create_denoised_cropped_pipe, create_cropped_denoised_pipe)

from macapype.pipelines.correct_bias import create_correct_bias_pipe
from macapype.pipelines.extract_brain import create_brain_extraction_pipe
from macapype.pipelines.segment import (create_brain_segment_pipe,
    create_full_segment_pipe)

data_path = "/hpc/meca/data/Macaques/Macaque_hiphop/"
#main_path = "/hpc/crise/meunier.d/Data/"
main_path = "/hpc/meca/users/loh.k/test_pipeline"
site = "sbri"
subject_ids = ['032311']

def create_infosource():
    infosource = pe.Node(interface=niu.IdentityInterface(fields=['subject_id']),name="infosource")
    infosource.iterables = [('subject_id', subject_ids)]

    return infosource

def create_datasource():
   datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],outfields=['T1','T2']),name = 'datasource')
   datasource.inputs.base_directory = data_path
   datasource.inputs.template = '%s/sub-%s/ses-001/%s/sub-%s_ses-001_run-*_%s.nii.gz'
   datasource.inputs.template_args = dict(
       T1=[[site,'subject_id',"anat",'subject_id',"T1w"]],
       T2=[[site,'subject_id',"anat",'subject_id',"T2w"]],
       )
   datasource.inputs.sort_filelist = True

   return datasource

###############################################################################
def create_segment_pnh_subpipes(name= "segment_pnh_subpipes",
                                crop_list = [(88, 144), (14, 180), (27, 103)],
                                sigma = 4):

    # creating pipeline
    seg_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1','T2']),
        name='inputnode')

    """
    old version (when we worked together a few months ago)
    - preproc
    - cropped_denoise
    - correct_bias
    - extract_brain
    - segment
    """

    ########### preprocessing (avg and align)
    preproc_pipe = create_average_align_pipe()

    seg_pipe.connect(inputnode,'T1',preproc_pipe,'inputnode.T1')
    seg_pipe.connect(inputnode,'T2',preproc_pipe,'inputnode.T2')

    ########### denoising and cropping
    denoise_pipe = create_cropped_denoised_pipe(crop_list = crop_list, sigma = sigma)

    seg_pipe.connect(preproc_pipe, "av_T1.avg_img", denoise_pipe,'inputnode.preproc_T1')
    seg_pipe.connect(preproc_pipe, "align_T2_on_T1.out_file", denoise_pipe,'inputnode.preproc_T2')

    ##### Correct_bias_T1_T2
    ### if denoised_cropped
    #correct_bias_pipe = create_correct_bias_pipe(sigma = sigma)

    #seg_pipe.connect(denoise_pipe, 'crop_bb_T1.roi_file',correct_bias_pipe,'inputnode.preproc_T1')
    #seg_pipe.connect(denoise_pipe, 'crop_bb_T2.roi_file',correct_bias_pipe,'inputnode.preproc_T2')

    ### if cropped_denoised
    correct_bias_pipe = create_correct_bias_pipe(sigma = sigma)

    seg_pipe.connect(denoise_pipe,'denoise_T1.denoised_img_file',correct_bias_pipe,'inputnode.preproc_T1')
    seg_pipe.connect(denoise_pipe,'denoise_T2.denoised_img_file',correct_bias_pipe,'inputnode.preproc_T2')


    ##### otherwise using nibabel node
    #from nodes.segment_pnh_nodes import correct_bias_T1_T2

    #correct_bias = pe.Node(interface = niu.Function(
        #input_names=["preproc_T1_file","preproc_T2_file", "sigma"],
        #output_names =  ["thresh_lower_file", "norm_mult_file", "bias_file", "smooth_bias_file", "restore_T1_file", "restore_T2_file"],
        #function = correct_bias_T1_T2),
        #name = "correct_bias")

    #correct_bias.inputs.sigma = sigma*2

    #seg_pipe.connect(preproc_pipe, 'crop_bb_T1.roi_file',correct_bias,'preproc_T1_file')
    #seg_pipe.connect(preproc_pipe, 'crop_bb_T2.roi_file',correct_bias,'preproc_T2_file')

    ####################
    brain_extraction_pipe = create_brain_extraction_pipe()

    seg_pipe.connect(correct_bias_pipe,'restore_T1.out_file', brain_extraction_pipe,"inputnode.restore_T1")
    seg_pipe.connect(correct_bias_pipe,'restore_T2.out_file', brain_extraction_pipe,"inputnode.restore_T2")

    ################### segment
    brain_segment_pipe = create_brain_segment_pipe()

    seg_pipe.connect(brain_extraction_pipe,"mult_T1.out_file",brain_segment_pipe,"inputnode.extracted_T1")

    return seg_pipe


###############################################################################

def create_segment_pnh_subpipes_new(name= "segment_pnh_subpipes",
                                crop_list = [(88, 144), (14, 180), (27, 103)],
                                sigma = 2):

    # creating pipeline
    seg_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1','T2']),
        name='inputnode')

    """
    new version (as it is now)
    - preproc
    - correct_bias
    - denoise_cropped
    - extract_brain
    - segment
    """

    #### preprocessing (avg and align)
    preproc_pipe = create_average_align_pipe()

    seg_pipe.connect(inputnode,'T1',preproc_pipe,'inputnode.T1')
    seg_pipe.connect(inputnode,'T2',preproc_pipe,'inputnode.T2')

    #### Correct_bias_T1_T2
    correct_bias_pipe = create_correct_bias_pipe(sigma = sigma)

    seg_pipe.connect(preproc_pipe, "av_T1.avg_img",correct_bias_pipe,'inputnode.preproc_T1')
    seg_pipe.connect(preproc_pipe, "align_T2_on_T1.out_file", correct_bias_pipe,'inputnode.preproc_T2')
    """
    ##### otherwise using nibabel node
    #from nodes.segment_pnh_nodes import correct_bias_T1_T2

    #correct_bias = pe.Node(interface = niu.Function(
        #input_names=["preproc_T1_file","preproc_T2_file", "sigma"],
        #output_names =  ["thresh_lower_file", "norm_mult_file", "bias_file", "smooth_bias_file", "restore_T1_file", "restore_T2_file"],
        #function = correct_bias_T1_T2),
        #name = "correct_bias")

    #correct_bias.inputs.sigma = sigma*2

    #seg_pipe.connect(preproc_pipe, 'crop_bb_T1.roi_file',correct_bias,'preproc_T1_file')
    #seg_pipe.connect(preproc_pipe, 'crop_bb_T2.roi_file',correct_bias,'preproc_T2_file')
    """

    #### denoising and cropping
    denoise_pipe = create_denoised_cropped_pipe(crop_list = crop_list)

    seg_pipe.connect(correct_bias_pipe, "restore_T1.out_file", denoise_pipe,'inputnode.preproc_T1')
    seg_pipe.connect(correct_bias_pipe, "restore_T2.out_file",denoise_pipe,'inputnode.preproc_T2')

    #### brain extraction
    brain_extraction_pipe = create_brain_extraction_pipe()

    #### si cropped_denoise
    ##seg_pipe.connect(denoise_pipe,'denoise_T1.denoised_img_file',brain_extraction_pipe,"inputnode.restore_T1")
    ##seg_pipe.connect(denoise_pipe,'denoise_T2.denoised_img_file',brain_extraction_pipe,"inputnode.restore_T2")

    #### si denoised_cropped
    seg_pipe.connect(denoise_pipe,'crop_bb_T1.roi_file',brain_extraction_pipe,"inputnode.restore_T1")
    seg_pipe.connect(denoise_pipe,'crop_bb_T2.roi_file',brain_extraction_pipe,"inputnode.restore_T2")

    ################### segment
    #brain_segment_pipe = create_brain_segment_pipe()
    #seg_pipe.connect(brain_extraction_pipe,"mult_T1.out_file",brain_segment_pipe,"inputnode.extracted_T1")

    ################### full_segment
    brain_segment_pipe = create_full_segment_pipe(crop_list = crop_list, sigma = sigma)

    seg_pipe.connect(preproc_pipe, "av_T1.avg_img",brain_segment_pipe,'inputnode.preproc_T1')
    seg_pipe.connect(preproc_pipe, "align_T2_on_T1.out_file", brain_segment_pipe,'inputnode.preproc_T2')

    seg_pipe.connect(brain_extraction_pipe,"smooth_mask.out_file",brain_segment_pipe,"inputnode.brain_mask")

    return seg_pipe

def create_main_workflow():

    main_workflow = pe.Workflow(name= "test_pipeline_kepkee_by_kepkee")
    main_workflow.base_dir = main_path

    ## Infosource
    infosource = create_infosource()

    ## Data source
    datasource = create_datasource()

    ## connect
    main_workflow.connect(infosource, 'subject_id', datasource, 'subject_id')

    ############################################## Preprocessing ################################
    ##### segment_pnh

    print('segment_pnh')

    #segment_pnh = create_segment_pnh_subpipes()
    segment_pnh = create_segment_pnh_subpipes_new()

    main_workflow.connect(datasource,'T1',segment_pnh,'inputnode.T1')
    main_workflow.connect(datasource,'T2',segment_pnh,'inputnode.T2')

    return main_workflow


if __name__ =='__main__':

    ### main_workflow
    wf = create_main_workflow()
    wf.write_graph(graph2use = "colored")
    wf.config['execution'] = {'remove_unnecessary_outputs':'false'}

    wf.run()
    #wf.run(plugin='MultiProc', plugin_args={'n_procs' : 2})
