#!/usr/bin/env python3
"""
    PNH anatomical segmentation pipeline given by Regis Trapeau warpped in
    Nipype.
    
    Description
    --------------
    TODO :/
    
    Arguments
    -----------
    -data:
        Path to the BIDS directory that contain subjects' MRI data.
        
    -resources:
        Path to the directory that contain resources (FSL/ and NMN_v1.2/).
        See 'Resources files' paragraph for further informations.
        
    -out:
        Nipype's processing directory. 
        It's where all the outputs will be saved.
        
    -subjects:
        IDs list of subjects to process.
    
    Example
    ---------
    python segment_pnh_regis.py -data [PATH_TO_BIDS] -out ../tests/ -subjects Elouk
    
    Resources files
    -----------------
    Brain templates are required to run this segmentation pipeline. Please,
    download the resources and specify the unzipped directory with the
    '-resources' argument in the command line.
    Resources are here:
    # TODO: find a permanent place
    https://cloud.int.univ-amu.fr/index.php/s/8bCJ5CWWPfHRyHs
    
    Requirements
    --------------
    This workflow use:
        - ANTS
        - SPM
        - FSL
    
"""

# Authors : David Meunier (david.meunier@univ-amu.fr)
#           Bastien Cagna (bastien.cagna@univ-amu.fr)
#           Regis Trapeau (regis.trapeau@univ-amu.fr)

import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.ants as ants
import nipype.interfaces.fsl as fsl

import os.path as op
import argparse

# from macapype.pipelines.correct_bias import create_debias_N4_pipe
# from macapype.nodes.correct_bias import interative_N4_debias
 
from macapype.nodes.denoise import nonlocal_denoise
from macapype.pipelines.register import create_iterative_register_pipe
from macapype.pipelines.extract_brain import create_old_segment_extraction_pipe
from macapype.utils.utils_tests import load_test_data

fsl.FSLCommand.set_default_output_type('NIFTI_GZ')


def create_infosource(subject_ids):
    infosource = pe.Node(
        interface=niu.IdentityInterface(fields=['subject_id']),
        name="infosource"
    )
    infosource.iterables = [('subject_id', subject_ids)]

    return infosource


def create_datasource(data_dir, sess):
    datasource = pe.Node(
        interface=nio.DataGrabber(infields=['subject_id'], outfields=['T1']),
        name='datasource'
    )
    datasource.inputs.base_directory = data_dir
    #datasource.inputs.template = '%s/sub-%s_ses-01_%s.nii'
    datasource.inputs.template = 'sub-%s/{}/anat/sub-%s_{}_%sCropped.nii'.format(sess, sess)
    datasource.inputs.template_args = dict(
        T1=[['subject_id', 'subject_id', "T1w"]],
    )
    datasource.inputs.sort_filelist = True
    
    return datasource


###############################################################################
def create_segment_pnh_onlyT1(nmt_file, nmt_ss_file, nmt_mask_file,
                              gm_prob_file, wm_prob_file, csf_prob_file,
                              name="segment_pnh_subpipes"):

    # creating pipeline
    seg_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1']),
        name='inputnode'
    )

    # Preprocessing (avg and align)
    # debias_pipe = create_debias_N4_pipe()
    # seg_pipe.connect(inputnode,'T1',debias_pipe,'inputnode.cropped_T1')

    # N4 correction
    debias_N4 = pe.Node(ants.N4BiasFieldCorrection(), name='debias_N4')
    seg_pipe.connect(inputnode, 'T1', debias_N4, 'input_image')

    # N4 correction
    # iterative_debias_N4 = pe.Node(
    #     niu.Function(
    #         input_names=['input_image','stop_param'],
    #         output_names=['debiased_image'],
    #         function=interative_N4_debias),
    #     name='iterative_debias_N4')
    #
    # seg_pipe.connect(inputnode,'T1',iterative_debias_N4,'input_image')
    # iterative_debias_N4.inputs.stop_param = 0.01

    denoise_T1 = pe.Node(
        niu.Function(input_names=["img_file"],
                     output_names=["denoised_img_file"],
                     function=nonlocal_denoise),
        name="denoise_T1"
    )
    seg_pipe.connect(debias_N4, 'output_image', denoise_T1, 'img_file')

    # TODO: Attention , brain extraction should come in between !!!

    bet = pe.Node(fsl.BET(), name='bet')
    bet.inputs.frac = 0.7
    # TODO: specify center (depending of the subject)
    # bet.inputs.center = [,,]
    seg_pipe.connect(denoise_T1, 'denoised_img_file', bet, 'in_file')

    # Register template to anat (need also skullstripped anat)
    # use iterative flirt
    iterative_register_pipe = create_iterative_register_pipe(
        template_file=nmt_file,
        template_brain_file=nmt_ss_file,
        template_mask_file=nmt_mask_file,
        gm_prob_file=gm_prob_file,
        wm_prob_file=wm_prob_file,
        csf_prob_file=csf_prob_file,
        n_iter=1
    )

    seg_pipe.connect(
        bet, 'out_file',
        iterative_register_pipe, "inputnode.anat_file_BET"
    )
    seg_pipe.connect(
        denoise_T1, 'denoised_img_file',
        iterative_register_pipe, 'inputnode.anat_file'
    )

    ## Compute brain mask using old_segment of SPM and postprocessing on
    ## tissues' masks
    #extract_brain = create_old_segment_extraction_pipe()
    #seg_pipe.connect(
        #iterative_register_pipe, 'register.anat_file_brain',
        #extract_brain, "inputnode.T1"
    #)
    #seg_pipe.connect(
        #iterative_register_pipe, 'merge_3_files.list3files',
        #extract_brain, "inputnode.seg_priors"
    #)

    return seg_pipe


###############################################################################
def create_main_workflow(data_dir, process_dir, subject_ids, sess, nmt_dir, 
                         nmt_fsl_dir):
    """ """
    nmt_file = op.join(nmt_dir, "NMT.nii.gz")
    nmt_ss_file = op.join(nmt_dir, "NMT_SS.nii.gz")
    nmt_mask_file = op.join(nmt_dir, 'masks', 'anatomical_masks',
                            'NMT_brainmask.nii.gz')

    gm_prob_file = op.join(nmt_fsl_dir, 'NMT_SS_pve_1.nii.gz')
    wm_prob_file = op.join(nmt_fsl_dir, 'NMT_SS_pve_2.nii.gz')
    csf_prob_file = op.join(nmt_fsl_dir, 'NMT_SS_pve_3.nii.gz')

    main_workflow = pe.Workflow(name="test_pipeline_regis")
    main_workflow.base_dir = process_dir

    print('adding info source and data source')
    # Infosource
    infosource = create_infosource(subject_ids)

    # Data source
    datasource = create_datasource(data_dir, sess)

    # connect
    main_workflow.connect(infosource, 'subject_id', datasource, 'subject_id')

    # *************************** Preprocessing ********************************
    # segment_pnh
    print('adding segment_pnh')
    segment_pnh = create_segment_pnh_onlyT1(
        nmt_file, nmt_ss_file, nmt_mask_file, gm_prob_file, wm_prob_file,
        csf_prob_file
    )
    main_workflow.connect(datasource, 'T1', segment_pnh, 'inputnode.T1')

    return main_workflow


################################################################################
def main(data_path, main_path, subjects, sess):
    data_path = op.abspath(data_path)
    #resources_dir = op.abspath(resources_dir)
    
    nmt_dir = load_test_data("NMT_v1.2")
    #nmt_dir = op.join(resources_dir, 'NMT_v1.2')
    
    # There also exists probabilistic maps in NMT_v1.2 folder,
    # do not know why Regis used these files he generated
    nmt_fsl_dir = load_test_data("NMT_FSL")
    
    # main_workflow
    print("Initialising the pipeline...")
    wf = create_main_workflow(
        data_dir=data_path,
        process_dir=main_path,
        subject_ids=subjects,
        sess=sess,
        nmt_dir=nmt_dir,
        nmt_fsl_dir=nmt_fsl_dir
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
        description="PNH segmenation pipeline from Regis Trapeau")
    parser.add_argument("-data", dest="data", type=str, required=True,
                        help="Directory containing MRI data (BIDS)")
    parser.add_argument("-out", dest="out", type=str,
                        help="Output directory", required=True)
    parser.add_argument("-sess", dest="sess", type=str,
                        help="Session", required=True)
    parser.add_argument("-subjects", dest="subjects", type=str, nargs='+',
                        help="Subjects' ID", required=True)
    args = parser.parse_args()
    
    main(
        data_path=args.data,
        main_path=args.out,
        subjects=args.subjects,
        sess=args.sess
    )

