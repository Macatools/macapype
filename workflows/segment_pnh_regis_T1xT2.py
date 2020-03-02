#!/usr/bin/env python3
"""
    PNH anatomical segmentation pipeline given by Regis Trapeau wrapped in
    Nipype.
    
    Description
    --------------
    TODO :/
    
    Arguments
    -----------
    -data:
        Path to the BIDS directory that contain subjects' MRI data.
        
    -out:
        Nipype's processing directory. 
        It's where all the outputs will be saved.
        
    -subjects:
        IDs list of subjects to process.

    -ses
        session (leave blank if None)
    
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

#import pybids
from bids.layout import BIDSLayout

from nipype.interfaces.io import BIDSDataGrabber

# from macapype.pipelines.correct_bias import create_debias_N4_pipe
from macapype.nodes.preproc import average_align
 
# from macapype.nodes.denoise import nonlocal_denoise
from macapype.nodes.bash_regis import (T1xT2BET, T1xT2BiasFieldCorrection,
                                       IterREGBET)

from macapype.pipelines.register import create_iterative_register_pipe
from macapype.pipelines.extract_brain import create_old_segment_extraction_pipe
from macapype.utils.utils_tests import load_test_data

#from macapype.utils.misc import get_first_elem

fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

data_inia = "/home/bastien/work/data/templates/inia19"
inia_brain_file = op.join(data_inia,"inia19-t1-brain.nii")


def create_infosource(subject_ids):
    infosource = pe.Node(
        interface=niu.IdentityInterface(fields=['subject_id']),
        name="infosource"
    )
    infosource.iterables = [('subject_id', subject_ids)]

    return infosource


def create_datasource(data_dir, sess):
    datasource = pe.Node(
        interface=nio.DataGrabber(infields=['subject_id'], outfields=['T1','T2']),
        name='datasource'
    )
    datasource.inputs.base_directory = data_dir
    datasource.inputs.template = 'sub-%s/{}/anat/sub-%s_{}_%s.nii'.format(sess, sess)
    datasource.inputs.template_args = dict(
        T1=[['subject_id', 'subject_id', "T1w"]],
        T2=[['subject_id', 'subject_id', "T2w"]],
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
        'T1': {"datatype": "anat", "suffix": "T1w", "extensions": ["nii",
                                                                   ".nii.gz"]},
        'T2': {"datatype": "anat", "suffix": "T2w", "extensions": ["nii",
                                                                   ".nii.gz"]}}

    layout = BIDSLayout(data_dir)
    print (layout)
    print(layout.get_subjects())
    print(layout.get_sessions())

    iterables = []
    if len(layout.get_subjects()) == 1:
         bids_datasource.inputs.subject = layout.get_subjects()[0]
    else:
        iterables.append(('subject', layout.get_subjects()[:2]))

    if len(layout.get_sessions()) == 1:
         bids_datasource.inputs.session = layout.get_sessions()[0]
    else:
        iterables.append(('session', layout.get_sessions()[:2]))

    if len(iterables):
        bids_datasource.iterables = iterables

    return bids_datasource

###############################################################################
#def create_segment_pnh_T1xT2(name="segment_pnh_subpipes"):
    ## creating pipeline
    #seg_pipe = pe.Workflow(name=name)

    ## creating inputnode
    #inputnode = pe.Node(
        #niu.IdentityInterface(fields=['T1','T2']),
        #name='inputnode'
    #)

    ## brain extraction + cropped
    #bet = pe.Node(T1xT2BET(m = True, aT2 = True, c = 10), name='bet')

    #seg_pipe.connect(inputnode, 'T1', bet, 't1_file')
    #seg_pipe.connect(inputnode, 'T2', bet, 't2_file')

    ## N4 correction
    #debias = pe.Node(T1xT2BiasFieldCorrection(), name='debias')

    #seg_pipe.connect(bet, 't1_cropped_file', debias, 't1_file')
    #seg_pipe.connect(bet, 't2_cropped_file', debias, 't2_file')

    #return seg_pipe

def create_segment_pnh_T1xT2(nmt_file, nmt_ss_file, nmt_mask_file,
                             gm_prob_file, wm_prob_file, csf_prob_file,
                             name="segment_pnh_subpipes_iterReg"):
    # Creating pipeline
    seg_pipe = pe.Workflow(name=name)

    # Creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1','T2']),
        name='inputnode'
    )

    # Brain extraction + cropped
    bet = pe.Node(T1xT2BET(m = True, aT2 = True, c = 10), name='bet')

    seg_pipe.connect(inputnode, 'T1', bet, 't1_file')
    seg_pipe.connect(inputnode, 'T2', bet, 't2_file')

    # iter reg
    reg = pe.Node(IterREGBET(), name='reg')

    seg_pipe.connect(bet, 't1_cropped_file', reg, 'inb_file')
    seg_pipe.connect(bet, 't1_brain_file', reg, 'inw_file')

    reg.inputs.refb_file = inia_brain_file

    ## N4 correction
    debias = pe.Node(T1xT2BiasFieldCorrection(), name='debias')

    seg_pipe.connect(bet, 't1_cropped_file', debias, 't1_file')
    seg_pipe.connect(bet, 't2_cropped_file', debias, 't2_file')
    seg_pipe.connect(reg, 'brain_mask_file', debias, 'b')

    # Register template to anat (need also skullstripped anat)
    # use iterative flirt
    iter_reg = create_iterative_register_pipe(
        template_file=nmt_file,
        template_brain_file=nmt_ss_file,
        template_mask_file=nmt_mask_file,
        gm_prob_file=gm_prob_file,
        wm_prob_file=wm_prob_file,
        csf_prob_file=csf_prob_file,
        n_iter=1
    )

    seg_pipe.connect(
        debias, 't1_cropped_file', iter_reg, "inputnode.anat_file_BET"
    )
    seg_pipe.connect(
        debias, 't1_debiased_file', iter_reg, 'inputnode.anat_file'
    )

    # Compute brain mask using old_segment of SPM and postprocessing on
    # tissues' masks
    extract_brain = create_old_segment_extraction_pipe()
    seg_pipe.connect(
        debias, 't1_debiased_file',
        extract_brain, "inputnode.T1"
    )
    seg_pipe.connect(
        iter_reg, 'merge_3_files.list3files',
        extract_brain, "inputnode.seg_priors"
    )

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

    main_workflow = pe.Workflow(name="test_pipeline_regis_T1xT2")
    main_workflow.base_dir = process_dir

    # Infosource

    if subject_ids is None or sess is None:
        print('adding BIDS data source')

        datasource = create_bids_datasource(data_dir)

    else:

        print('adding info source and data source')
        infosource = create_infosource(subject_ids)

        # Data source
        datasource = create_datasource(data_dir, sess)

        # connect
        main_workflow.connect(infosource, 'subject_id', datasource, 'subject_id')


    # *************************** Preprocessing ********************************
    # segment_pnh
    print('adding segment_pnh')
    segment_pnh = create_segment_pnh_T1xT2()

    #main_workflow.connect(datasource, 'T1', segment_pnh, 'inputnode.T1')
    main_workflow.connect(datasource, ('T1', average_align), segment_pnh, 'inputnode.T1')
    main_workflow.connect(datasource, ('T2', average_align), segment_pnh, 'inputnode.T2')

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
    #wf.write_graph(graph2use="colored")
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
                        help="Session", required=False)
    parser.add_argument("-subjects", dest="subjects", type=str, nargs='+',
                        help="Subjects' ID", required=False)

    args = parser.parse_args()
    
    main(
        data_path=args.data,
        main_path=args.out,
        subjects=args.subjects,
        sess=args.sess
    )

