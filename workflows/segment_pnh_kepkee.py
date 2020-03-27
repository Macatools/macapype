#!/usr/bin/env python3
"""
    PNH anatomical segmentation pipeline given by Kepkee Loh wrapped in
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
        - ANTS
        - AFNI
        - FSL

"""

# Authors : David Meunier (david.meunier@univ-amu.fr)
#           Bastien Cagna (bastien.cagna@univ-amu.fr)
#           Kepkee Loh (kepkee.loh@univ-amu.fr)
#           Julien Sein (julien.sein@univ-amu.fr)

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

from macapype.pipelines.full_segment import create_full_segment_pnh_subpipes

from macapype.utils.utils_tests import load_test_data


my_path = "/hpc/crise/meunier.d"

nmt_dir = load_test_data('NMT_v1.2', path_to = my_path)
atlasbrex_dir = load_test_data('AtlasBREX', path_to = my_path)

def create_datasource(data_dir, subjects=None, sessions=None, acqs=None):
    """ Create a datasource node that have iterables following BIDS format """
    bids_datasource = pe.Node(
        interface=nio.BIDSDataGrabber(),
        name='bids_datasource'
    )

    bids_datasource.inputs.base_dir = data_dir
    bids_datasource.inputs.output_query = {
        'T1': {
            "datatype": "anat", "suffix": "T1w",
            "extensions": ["nii", ".nii.gz"]
        },
        'T2': {
            "datatype": "anat", "suffix": "T2w",
            "extensions": ["nii", ".nii.gz"]
        }
    }

    layout = BIDSLayout(data_dir)

    # Verbose
    print("BIDS layout:", layout)
    print("\t", layout.get_subjects())
    print("\t", layout.get_sessions())

    #print("\t", layout.get_acquisitions())



    if subjects is None:
        subjects = layout.get_subjects()

    if sessions is None:
        sessions = layout.get_sessions()

    iterables = []
    iterables.append(('subject', subjects))
    iterables.append(('session', sessions))

    if acqs is not None:
        iterables.append(('acquisition', acqs))

    bids_datasource.iterables = iterables

    return bids_datasource

###############################################################################

def create_main_workflow(data_dir, process_dir, subject_ids, ses):

    main_workflow = pe.Workflow(name= "test_pipeline_kepkee_crop")
    main_workflow.base_dir = process_dir


    datasource = create_datasource(data_dir, subject_ids, sessions)

    ############################################## Preprocessing ################################
    ##### segment_pnh

    print('segment_pnh_kepkee')

    segment_pnh = create_full_segment_pnh_subpipes()

    main_workflow.connect(datasource,'T1',segment_pnh,'inputnode.T1')
    main_workflow.connect(datasource,'T2',segment_pnh,'inputnode.T2')

    return main_workflow

if __name__ == '__main__':

    # Command line parser
    parser = argparse.ArgumentParser(
        description="PNH segmentation pipeline from Kepkee Loh / Julien Sein")

    parser.add_argument("-data", dest="data", type=str, required=True,
                        help="Directory containing MRI data (BIDS)")
    parser.add_argument("-out", dest="out", type=str, #nargs='+',
                        help="Output dir", required=True)
    parser.add_argument("-ses", dest="ses", type=str,
                        help="Session", required=False)
    parser.add_argument("-subjects", dest="subjects", type=str, nargs='+',
                        help="Subjects' ID", required=False)

    args = parser.parse_args()

    # main_workflow
    print("Initialising the pipeline...")
    wf = create_main_workflow(
        data_dir=args.data,
        process_dir=args.out,
        subject_ids=args.subjects,
        ses=args.ses
    )
    wf.write_graph(graph2use="colored")
    wf.config['execution'] = {'remove_unnecessary_outputs': 'false'}
    print('The PNH segmentation pipeline is ready')

    print("Start to process")
    wf.run()
    # wf.run(plugin='MultiProc', plugin_args={'n_procs' : 2})
