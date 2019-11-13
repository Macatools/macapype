import os
import os.path as op

import argparse


import nipype

import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

from macapype.pipelines.preproc import create_average_align_cropped_pipe
from macapype.pipelines.denoise import create_denoised_pipe

from macapype.pipelines.correct_bias import create_correct_bias_pipe
from macapype.pipelines.extract_brain import create_brain_extraction_pipe
from macapype.pipelines.segment import create_full_segment_pipe

from macapype.utils.misc import show_files
from macapype.utils.utils_tests import load_test_data

nmt_dir = load_test_data('NMT_v1.2')
atlasbrex_dir = load_test_data('AtlasBREX')

def create_infosource(subject_ids):
    infosource = pe.Node(interface=niu.IdentityInterface(fields=['subject_id']),name="infosource")
    infosource.iterables = [('subject_id', subject_ids)]

    return infosource


def create_datasource(data_dir):
    datasource = pe.Node(
        interface=nio.DataGrabber(infields=['subject_id'], outfields=['T1', 'T1cropbox', 'T2']),
        name='datasource'
    )
    datasource.inputs.base_directory = data_dir
    #datasource.inputs.template = '%s/sub-%s_ses-01_%s.nii'
    datasource.inputs.template = 'sub-%s/ses-01/sub-%s_ses-01_%s.%s'
    datasource.inputs.template_args = dict(
        T1=[['subject_id','subject_id', "mp2rageT1w", "nii.gz"]],
        T1cropbox=[['subject_id', 'subject_id', "mp2rageT1wCropped", "cropbox"]],
        T2=[['subject_id', 'subject_id', "T2w", "nii.gz"]],
    )
    datasource.inputs.sort_filelist = True

    return datasource


#def create_datasource(data_dir):
   #datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],outfields=['T1','T2']),name = 'datasource')
   #datasource.inputs.base_directory = "/hpc/meca/"
   #datasource.inputs.template = '%s/%s/%s%s/%s/%s/sub-%s_ses-001_run-*_%s.nii.gz'
   #datasource.inputs.template_args = dict(
       #T1=[["data/Macaques/Macaque_hiphop/",site,"sub-",'subject_id',"ses-001","anat",'subject_id',"T1w"]],
       #T2=[["data/Macaques/Macaque_hiphop/",site,"sub-",'subject_id',"ses-001","anat",'subject_id',"T2w"]]
       #)
   #datasource.inputs.sort_filelist = True

   #return datasource


###############################################################################

def create_segment_pnh_subpipes(name= "segment_pnh_subpipes",
                                sigma = 2):

    # creating pipeline
    seg_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1', 'T1cropbox', 'T2']),
        name='inputnode')

    """
    new version (as it is now)
    - preproc
    - correct_bias
    - denoise_cropped
    - extract_brain
    - segment
    """

    #### preprocessing (avg and align, and crop)
    preproc_pipe = create_average_align_cropped_pipe()

    seg_pipe.connect(inputnode,'T1',preproc_pipe,'inputnode.T1')
    seg_pipe.connect(inputnode,'T2',preproc_pipe,'inputnode.T2')

    seg_pipe.connect(inputnode,'T1cropbox',preproc_pipe,'inputnode.T1cropbox')
    seg_pipe.connect(inputnode,'T1cropbox',preproc_pipe,'inputnode.T2cropbox')

    #### Correct_bias_T1_T2
    correct_bias_pipe = create_correct_bias_pipe(sigma = sigma)

    seg_pipe.connect(preproc_pipe, "crop_bb_T1.roi_file",correct_bias_pipe,'inputnode.preproc_T1')
    seg_pipe.connect(preproc_pipe, "crop_bb_T2.roi_file", correct_bias_pipe,'inputnode.preproc_T2')

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
    denoise_pipe = create_denoised_pipe()

    seg_pipe.connect(correct_bias_pipe, "restore_T1.out_file", denoise_pipe,'inputnode.preproc_T1')
    seg_pipe.connect(correct_bias_pipe, "restore_T2.out_file",denoise_pipe,'inputnode.preproc_T2')


    #### brain extraction
    brain_extraction_pipe = create_brain_extraction_pipe(
        atlasbrex_dir=atlasbrex_dir, nmt_dir=nmt_dir, name = "devel_atlas_brex")

    seg_pipe.connect(denoise_pipe,'denoise_T1.denoised_img_file',brain_extraction_pipe,"inputnode.restore_T1")
    seg_pipe.connect(denoise_pipe,'denoise_T2.denoised_img_file',brain_extraction_pipe,"inputnode.restore_T2")

    ################### segment (restarting from skull-stripped T1)
    # (segmentation is done NMT template space for now)
    #brain_segment_pipe = create_brain_segment_pipe(
       #NMT_file, NMT_brainmask_prob, NMT_brainmask, NMT_brainmask_CSF,
       #NMT_brainmask_GM, NMT_brainmask_WM)

    #seg_pipe.connect(brain_extraction_pipe,"mult_T1.out_file",brain_segment_pipe,"inputnode.extracted_T1")

    ################### full_segment (restarting from the avg_align files,)
    brain_segment_pipe = create_full_segment_pipe(sigma=sigma, nmt_dir = nmt_dir,
        name="segment_devel_NMT_sub_align")

    seg_pipe.connect(preproc_pipe, "crop_bb_T1.roi_file",brain_segment_pipe,'inputnode.preproc_T1')
    seg_pipe.connect(preproc_pipe, "crop_bb_T1.roi_file", brain_segment_pipe,'inputnode.preproc_T2')

    seg_pipe.connect(brain_extraction_pipe,"smooth_mask.out_file",brain_segment_pipe,"inputnode.brain_mask")

    return seg_pipe

def create_main_workflow(data_dir, process_dir, subject_ids):

    main_workflow = pe.Workflow(name= "test_pipeline_kepkee")
    main_workflow.base_dir = process_dir

    ## Infosource
    infosource = create_infosource(subject_ids)

    ## Data source
    datasource = create_datasource(data_dir)

    ## connect
    main_workflow.connect(infosource, 'subject_id', datasource, 'subject_id')

    ############################################## Preprocessing ################################
    ##### segment_pnh

    print('segment_pnh')

    segment_pnh = create_segment_pnh_subpipes()

    main_workflow.connect(datasource,'T1',segment_pnh,'inputnode.T1')
    main_workflow.connect(datasource,'T1cropbox',segment_pnh,'inputnode.T1cropbox')
    main_workflow.connect(datasource,'T2',segment_pnh,'inputnode.T2')

    return main_workflow


def main(data_path, main_path, subjects):
    #data_path = op.abspath(data_path)
    #main_path = op.abspath(main_path)

    #nmt_dir = load_test_data("NMT_v1.2")
    #nmt_dir = op.join(resources_dir, 'NMT_v1.2')

    # There also exists probabilistic maps in NMT_v1.2 folder,
    # do not know why Regis used these files he generated
    #nmt_fsl_dir = load_test_data("NMT_FSL")

    # main_workflow
    print("Initialising the pipeline...")
    wf = create_main_workflow(
        data_dir=data_path,
        process_dir=main_path,
        subject_ids=subjects
    )
    wf.write_graph(graph2use="colored")
    wf.config['execution'] = {'remove_unnecessary_outputs': 'false'}
    print('The PNH segmentation pipeline is ready')

    print("Start to process")
    wf.run()
    # wf.run(plugin='MultiProc', plugin_args={'n_procs' : 2})



if __name__ == '__main__':
    # Command line parser
    parser = argparse.ArgumentParser(
        description="PNH segmenation pipeline from Kepkee Loh / Julien Sein")

    parser.add_argument("-data", dest="data", type=str, required=True,
                        help="Directory containing MRI data (BIDS)")
    parser.add_argument("-out", dest="out", type=str, #nargs='+',
                        help="Output dir", required=True)
    parser.add_argument("-subjects", dest="subjects", type=str, nargs='+',
                        help="Subjects' ID", required=True)
    args = parser.parse_args()

    main(
        data_path=args.data,
        main_path=args.out,
        subjects=args.subjects
    )
