#!/usr/bin/env python3
"""
    Non humain primates anatomical segmentation pipeline based ANTS

    Adapted in Nipype from an original pipelin of Kepkee Loh wrapped.
    
    Description
    --------------
    Using T1w coupled with a T2w, this pipeline uses FSL for all basic 
    operations, ANTs for non-linear registration and SPM for segmentation (no 
    need to have matlab with docker). To do it, the inputs don't need to be 
    pre-processed (raw files) but it needs a template (any template, that's why 
    it works with humans too).
    All outputs are rigidly aligned with the chosen template and also cropped as
    the template (the big advantage is that the anat is in a standard 
    orientation).
    
    Arguments
    -----------
    -data:
        Path to the BIDS directory that contain subjects' MRI data.
        
    -out:
        Nipype's processing directory. 
        It's where all the outputs will be saved.
        
    -subjects:
        IDs list of subjects to process.

    -ses (optional)
       Session

    -acq (optional)
       Acquisition name
    
    Example
    ---------
    python segment_pnh_spm_based.py -data [PATH_TO_BIDS] -out [PATH_TO_OUT] -ses 01 -acq 0p4mm -subjects Elouk
    
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
        - ANTS
        - SPM

    Notes
    -----
    If you do not use Matlab, remeber that you can use the standalone version of SPM.
    
"""

# Authors : David Meunier (david.meunier@univ-amu.fr)
#           Bastien Cagna (bastien.cagna@univ-amu.fr)
#           Regis Trapeau (regis.trapeau@univ-amu.fr)

import os
import os.path as op
import argparse
import json
import pprint

import nipype.interfaces.fsl as fsl
import nipype.pipeline.engine as pe

from macapype.pipelines.full_pipelines import (
    create_full_T1xT2_segment_pnh_subpipes)
from macapype.utils.utils_tests import load_test_data, format_template
from macapype.utils.utils_bids import create_datasource


fsl.FSLCommand.set_default_output_type('NIFTI_GZ')


################################################################################
def create_main_workflow(data_path, out_path, subject_ids, sessions,
                         acquisitions, params_file):
    """ Set up the segmentatiopn pipeline based on SPM 
    
    Arguments
    ---------
    data_path: pathlike str
        Path to the BIDS directory that contains anatomical images

    out_path: pathlike str
        Path to the ouput directory (will be created if not alredy existing).
        Previous outputs maybe overwritten.

    params_file: path to a JSON file
        JSON file that specify some parameters of the pipeline.

    subjects_ids: list of str
        Subject's IDs to match to BIDS specification (sub-[SUB1], sub-[SUB2]...)

    sessions: list of str (optional)
        Session's IDs to match to BIDS specification (ses-[SES1], ses-[SES2]...)    

    acquisitions: list of str (optional)
        Acquisition name to match to BIDS specification (acq-[ACQ1]...)

    Returns
    -------
    workflow: nipype.pipeline.engine.Workflow
    

    """

    # Make sure the data path is an absolute path
    data_path = op.abspath(data_path)

    # If not already existing, create the output path
    if not op.isdir(out_path):
        os.makedirs(out_path)

    # Make sure that params file exists if specified
    if params_file is not None:
        assert os.path.exists(params_file), "Error with file {}".format(
            params_file)
        params = json.load(open(params_file))
    else:
        params = {}

    # Print params
    print(" ******************* PARAMS ******************* ")
    print(params)
    pprint.pprint(params)
    print(" ********************************************** ")

    # If no value is given for template name, set fedault value to inia19
    if "general" in params.keys() and "template_name" in params["general"].keys():
        template_name = params["general"]["template_name"]
    else:
        template_name = 'inia19'

    # Make sure that template are downloaded
    nmt_dir = load_test_data(template_name)

    
    params_template = format_template(nmt_dir, template_name)
    print (params_template)

    # Create the Nipype workflow
    workflow = pe.Workflow(name="T1xT2_processing_workflow_json_template")
    workflow.base_dir = out_path

    # First, get the data using a BIDS data grabber
    datasource = create_datasource(data_path, subject_ids, sessions,
                                   acquisitions)

    # Then, add the segmentation pipeline
    segment_pnh = create_full_T1xT2_segment_pnh_subpipes(params_template, params)

    # And finally, connect the data grabber with the processing node
    workflow.connect(
        datasource, 'T1', segment_pnh, 'inputnode.T1')
    workflow.connect(
        datasource, 'T2', segment_pnh, 'inputnode.T2')

    return workflow


################################################################################
def main():
    """ Command line interpreter for PNH segmentation based on SPM """

    # Command line parser
    parser = argparse.ArgumentParser(
        description="PNH segmentation pipeline from Regis Trapeau")
    parser.add_argument("-data", dest="data", type=str, required=True,
                        help="Directory containing MRI data (BIDS)")
    parser.add_argument("-out", dest="out", type=str,
                        help="Output directory", required=True)
    parser.add_argument("-params", dest="params_file", type=str,
                        help="Parameters json file", required=False)
    parser.add_argument("-subjects", dest="subjects", type=str, nargs='+',
                        help="Subjects' ID", required=False)
    parser.add_argument("-ses", dest="ses", type=str, nargs='+', default=None,
                        help="Sessions ID")
    parser.add_argument("-acq", dest="acq", type=str, nargs='+', default=None,
                        help="Acquisitions ID")

    args = parser.parse_args()

    # Create the workflow
    print("Initialising the pipeline...")
    wf = create_main_workflow(
        data_path=args.data,
        main_path=args.out,
        subject_ids=args.subjects,
        acquisitions=args.acq,
        sessions=args.ses,
        params_file=args.params_file
    )
    wf.config['execution'] = {'remove_unnecessary_outputs': 'false'}

    # Go!
    print('The PNH segmentation pipeline is ready. Start to process")
    wf.run()


if __name__ == '__main__':
    main()

