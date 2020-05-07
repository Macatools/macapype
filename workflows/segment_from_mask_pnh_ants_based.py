
import os
import argparse


import nipype
import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

from macapype.pipelines.segment import create_full_segment_from_mask_pipe

from macapype.utils.misc import show_files

from macapype.utils.utils_tests import load_test_data

#data_path = "/hpc/meca/data/Macaques/Macaque_hiphop/"
#main_path = "/hpc/crise/meunier.d/Data/"

nmt_dir = load_test_data('NMT_v1.2')

def create_infosource(subject_ids):
    infosource = pe.Node(interface=niu.IdentityInterface(fields=['subject_id']),name="infosource")
    infosource.iterables = [('subject_id', subject_ids)]

    return infosource

#main_path = "/hpc/meca/users/loh.k/macaque_preprocessing/preproc_macapype/test_pipeline_kepkee_ucdavid/segment_pnh_subpipes"



def create_datasource_preproc_cropped_by_macapype(data_dir, ses):
   datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],outfields=['T1','T2', 'mask']),name = 'datasource')
   datasource.inputs.base_directory = data_dir
    datasource.inputs.template = 'sub-%s/{}/anat/sub-%s_*run-*_%s.%s'.format(ses)
   datasource.inputs.template_args = dict(
       T1=[["average_align_pipe","_subject_id_", 'subject_id',"","crop_bb_T1","*",
            'subject_id',"T1w_roi"]],
       T2=[["average_align_pipe","_subject_id_", 'subject_id',"","crop_bb_T2",
            "*",'subject_id',"T2w_flirt_roi"]],
       mask=[["devel_atlas_brex", "_subject_id_",
              'subject_id', "","smooth_mask", "*", 'subject_id',
              'T1w_roi_maths_noise_corrected_brain_bin_bin_nice']],
              #'T1w_maths_aonlm_denoised_roi_brain_bin_bin']],
       )
   datasource.inputs.sort_filelist = True

   return datasource


def create_datasource_preproc_by_macapype(data_dir, ses):
   datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],outfields=['T1','T2', 'mask']),name = 'datasource')
   datasource.inputs.base_directory = data_dir
    datasource.inputs.template = 'sub-%s/{}/anat/sub-%s_*run-*_%s.%s'.format(ses)
   datasource.inputs.template_args = dict(
       T1=[["average_align_pipe","_subject_id_", 'subject_id',"","crop_bb_T1","*",
            'subject_id',"T1w"]],
       T2=[["average_align_pipe","_subject_id_", 'subject_id',"","crop_bb_T2",
            "*",'subject_id',"T2w_flirt"]],
       mask=[["devel_atlas_brex", "_subject_id_",
              'subject_id', "","smooth_mask", "*", 'subject_id',
              'T1w_roi_maths_noise_corrected_brain_bin_bin_nice']],
              #'T1w_maths_aonlm_denoised_roi_brain_bin_bin']],
       )
   datasource.inputs.sort_filelist = True

   return datasource



#data_path = "/hpc/meca/users/loh.k/macaque_preprocessing/preprocessed_030419/"
#main_path = "/hpc/meca/users/loh.k/test_pipeline"

#def create_datasource_preproc_by_bash():
   #datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],outfields=['T1','T2', 'mask']),name = 'datasource')
   #datasource.inputs.base_directory = data_path
   #datasource.inputs.template = '%s_%s/%s_%s_%s.nii.gz'
   #datasource.inputs.template_args = dict(
       #T1=[[site,'subject_id',site,'subject_id','t1']],
       #T2=[[site,'subject_id',site,'subject_id','t2']],
       #mask=[[site,'subject_id',site,'subject_id','brainmask']])
       ##mask=[[site,'subject_id',site,'subject_id','brainmask_nice']])
   #datasource.inputs.sort_filelist = True

   #return datasource

###############################################################################

def create_main_workflow(data_dir, process_dir, subject_ids, ses, crop_req):

    main_workflow = pe.Workflow(name= "test_pipeline_segment_from_mask")
    main_workflow.base_dir = data_dir

    #if subject_ids is None or sess is None:
        #print('adding BIDS data source')
        #datasource = create_bids_datasource(data_dir)
        #print(datasource.outputs)

    #else:

    print('adding infosource and datasource')

    # Infosource
    infosource = create_infosource(subject_ids)

    ## Data source
    if crop_req:
        datasource = create_datasource_preproc_cropped_by_macapype(data_dir, ses)
    else:
        datasource = create_datasource_preproc_by_macapype(data_dir, ses) # if done with other
    # script segment_pnh_kepkee.py

    #datasource = create_datasource_preproc_by_bash() # if done with bash
    # script

    # connect
    main_workflow.connect(infosource, 'subject_id', datasource, 'subject_id')



    ############################ Preprocessing ################################
    ##### segment_pnh

    print('full_segment_pnh')

    ################### full_segment

    brain_segment_pipe = create_full_segment_from_mask_pipe(sigma=2, nmt_dir = nmt_dir,
        name="segment_from_mask")

    main_workflow.connect(datasource, "T1",brain_segment_pipe,'inputnode.preproc_T1')
    main_workflow.connect(datasource, "T2", brain_segment_pipe,'inputnode.preproc_T2')

    main_workflow.connect(datasource,"mask",brain_segment_pipe,"inputnode.brain_mask")

    return main_workflow



if __name__ == '__main__':

    # Command line parser
    parser = argparse.ArgumentParser(
        description="PNH segmentation pipeline from Kepkee Loh / Julien Sein")

    parser.add_argument("-data", dest="data", type=str, required=True,
                        help="Directory containing MRI data (BIDS)")
    parser.add_argument("-out", dest="out", type=str, #nargs='+',
                        help="Output dir", required=True)
    parser.add_argument("-sess", dest="sess", type=str,
                        help="Session", required=False)
    parser.add_argument("-subjects", dest="subjects", type=str, nargs='+',
                        help="Subjects' ID", required=False)
    parser.add_argument("-crop_req", dest="crop_req", default = True,
                        action='store_false', help="The Cropping was done by Macapype")

    args = parser.parse_args()

    # main_workflow
    print("Initialising the pipeline...")
    wf = create_main_workflow(
        data_dir=args.data,
        process_dir=args.out,
        subject_ids=args.subjects,
        ses=args.ses,
        crop_req=args.crop_req
    )
    wf.write_graph(graph2use="colored")
    wf.config['execution'] = {'remove_unnecessary_outputs': 'false'}
    print('The PNH segmentation pipeline is ready')

    print("Start to process")
    wf.run()
    # wf.run(plugin='MultiProc', plugin_args={'n_procs' : 2})
