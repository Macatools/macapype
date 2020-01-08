import os
import os.path as op

import argparse


import nipype

import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

#import pybids
from bids.layout import BIDSLayout
from nipype.interfaces.io import BIDSDataGrabber

from macapype.pipelines.preproc import (create_average_align_cropped_pipe,
                                        create_average_align_pipe)

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


def create_datasource(data_dir, sess):
    datasource = pe.Node(
        interface=nio.DataGrabber(infields=['subject_id'], outfields=['T1', 'T1cropbox', 'T2']),
        name='datasource'
    )
    datasource.inputs.base_directory = data_dir
    #datasource.inputs.template = '%s/sub-%s_ses-01_%s.nii'
    datasource.inputs.template = 'sub-%s/{}/sub-%s_{}_%s.%s'.format(sess, sess)
    datasource.inputs.template_args = dict(
        T1=[['subject_id','subject_id', "mp2rageT1w", "nii"]],
        T1cropbox=[['subject_id', 'subject_id', "mp2rageT1wCropped", "cropbox"]],
        T2=[['subject_id', 'subject_id', "T2w", "nii"]],
    )
    datasource.inputs.sort_filelist = True

    return datasource

def create_bids_datasource(data_dir):

    bids_datasource = pe.Node(
        interface=nio.BIDSDataGrabber(),
        name='bids_datasource'
    )

    bids_datasource.inputs.base_dir = data_dir
    bids_datasource.inputs.output_query = {
        'T1': {"datatype": "anat",
               "suffix": "T1w",
               "extensions": ["nii", ".nii.gz"]},
        'T2': {"datatype": "anat",
               "suffix": "T2w",
               "extensions": ["nii", ".nii.gz"]}}

    layout = BIDSLayout(data_dir)
    print (layout)
    print(layout.get_subjects())
    print(layout.get_sessions())


    iterables = []

    assert len(layout.get_subjects()) or len(layout.get_sessions()), \
        "Error, BIDS dir should have at least one subject and one session"

    if len(layout.get_subjects()) == 1:
         bids_datasource.inputs.subject = layout.get_subjects()[0]
    else:
        iterables.append(('subject', layout.get_subjects()))

    if len(layout.get_sessions()) == 1:
         bids_datasource.inputs.session = layout.get_sessions()[0]
    else:
        iterables.append(('session', layout.get_sessions()))

    if len(iterables):
        bids_datasource.iterables = iterables

    return bids_datasource

###############################################################################

def create_segment_pnh_subpipes(name= "segment_pnh_subpipes",
                                sigma = 2, cropped = True):

    # creating pipeline
    seg_pipe = pe.Workflow(name=name)

    """
    new version (as it is now)
    - preproc (avg and align, crop is optional)
    - correct_bias
    - denoise
    - extract_brain
    - segment
    """
    print("Cropped:", cropped)

    if cropped:

        inputnode = pe.Node(
            niu.IdentityInterface(fields=['T1', 'T2']),
            name='inputnode')

        #### preprocessing (avg and align)
        preproc_pipe = create_average_align_pipe()

        seg_pipe.connect(inputnode,'T1',preproc_pipe,'inputnode.T1')
        seg_pipe.connect(inputnode,'T2',preproc_pipe,'inputnode.T2')

        return seg_pipe

        #### Correct_bias_T1_T2
        correct_bias_pipe = create_correct_bias_pipe(sigma = sigma)

        seg_pipe.connect(preproc_pipe, "av_T1.avg_img", correct_bias_pipe,'inputnode.preproc_T1')
        seg_pipe.connect(preproc_pipe, "align_T2_on_T1.out_file", correct_bias_pipe,'inputnode.preproc_T2')

    else:

        inputnode = pe.Node(
            niu.IdentityInterface(fields=['T1', 'T1cropbox', 'T2']),
            name='inputnode')

        #### preprocessing (avg and align)
        preproc_pipe = create_average_align_cropped_pipe()

        seg_pipe.connect(inputnode,'T1',preproc_pipe,'inputnode.T1')
        seg_pipe.connect(inputnode,'T2',preproc_pipe,'inputnode.T2')

        seg_pipe.connect(inputnode,'T1cropbox',preproc_pipe,'inputnode.T1cropbox')
        seg_pipe.connect(inputnode,'T1cropbox',preproc_pipe,'inputnode.T2cropbox')

        return seg_pipe

        #### Correct_bias_T1_T2
        correct_bias_pipe = create_correct_bias_pipe(sigma = sigma)

        seg_pipe.connect(preproc_pipe, "crop_bb_T1.roi_file",correct_bias_pipe,'inputnode.preproc_T1')
        seg_pipe.connect(preproc_pipe, "crop_bb_T2.roi_file", correct_bias_pipe,'inputnode.preproc_T2')

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


    #### denoising
    denoise_pipe = create_denoised_pipe()

    seg_pipe.connect(correct_bias_pipe, "restore_T1.out_file", denoise_pipe,'inputnode.preproc_T1')
    seg_pipe.connect(correct_bias_pipe, "restore_T2.out_file",denoise_pipe,'inputnode.preproc_T2')


    ##### brain extraction
    brain_extraction_pipe = create_brain_extraction_pipe(
        atlasbrex_dir=atlasbrex_dir, nmt_dir=nmt_dir, name = "devel_atlas_brex")

    seg_pipe.connect(denoise_pipe,'denoise_T1.denoised_img_file',brain_extraction_pipe,"inputnode.restore_T1")
    seg_pipe.connect(denoise_pipe,'denoise_T2.denoised_img_file',brain_extraction_pipe,"inputnode.restore_T2")

    # (if no denoise)
    #seg_pipe.connect(correct_bias_pipe,'restore_T1.out_file',brain_extraction_pipe,"inputnode.restore_T1")
    #seg_pipe.connect(correct_bias_pipe,'restore_T2.out_file',brain_extraction_pipe,"inputnode.restore_T2")

    ################### segment (restarting from skull-stripped T1) old version
    #(segmentation is done NMT template space for now)
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

def create_main_workflow(data_dir, process_dir, subject_ids, sess, cropped):

    main_workflow = pe.Workflow(name= "test_pipeline_kepkee_denoise_cropped")
    main_workflow.base_dir = process_dir

    if subject_ids is None or sess is None and cropped is not None:
        print('adding BIDS data source')
        datasource = create_bids_datasource(data_dir)
        print(datasource.outputs)

    else:
        print('adding infosource and datasource')

        # Infosource
        infosource = create_infosource(subject_ids)

        # Data source
        datasource = create_datasource(data_dir, sess)

        # connect
        main_workflow.connect(infosource, 'subject_id', datasource, 'subject_id')




    ############################################## Preprocessing ################################
    ##### segment_pnh

    print('segment_pnh')

    segment_pnh = create_segment_pnh_subpipes(cropped = cropped)

    main_workflow.connect(datasource,'T1',segment_pnh,'inputnode.T1')
    main_workflow.connect(datasource,'T2',segment_pnh,'inputnode.T2')

    if cropped is not True:
        main_workflow.connect(datasource,'T1cropbox',segment_pnh,'inputnode.T1cropbox')

    return main_workflow

if __name__ == '__main__':

    # Command line parser
    parser = argparse.ArgumentParser(
        description="PNH segmenation pipeline from Kepkee Loh / Julien Sein")

    parser.add_argument("-data", dest="data", type=str, required=True,
                        help="Directory containing MRI data (BIDS)")
    parser.add_argument("-out", dest="out", type=str, #nargs='+',
                        help="Output dir", required=True)
    parser.add_argument("-sess", dest="sess", type=str,
                        help="Session", required=False)
    parser.add_argument("-subjects", dest="subjects", type=str, nargs='+',
                        help="Subjects' ID", required=False)
    parser.add_argument("-cropped", dest="cropped", type=bool,
                        help="Already Cropped", required=False)

    args = parser.parse_args()

    # main_workflow
    print("Initialising the pipeline...")
    wf = create_main_workflow(
        data_dir=args.data,
        process_dir=args.out,
        subject_ids=args.subjects,
        sess=args.sess,
        cropped=args.cropped
    )
    wf.write_graph(graph2use="colored")
    wf.config['execution'] = {'remove_unnecessary_outputs': 'false'}
    print('The PNH segmentation pipeline is ready')

    print("Start to process")
    wf.run()
    # wf.run(plugin='MultiProc', plugin_args={'n_procs' : 2})
