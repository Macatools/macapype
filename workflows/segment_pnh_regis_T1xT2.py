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
    python segment_pnh_regis_T1xT2.py -data /home/bastien/work/data/local_primavoice -out /home/bastien/work/projects/macapype/local_tests -template /home/bastien/work/data/templates/inia19/inia19-t1-brain.nii -priors /home/bastien/work/data/templates/inia19/inia19-prob_0.nii /home/bastien/work/data/templates/inia19/inia19-prob_1.nii /home/bastien/work/data/templates/inia19/inia19-prob_2.nii -ses 01 -sub Maga
    
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

import os
import os.path as op
import argparse
import json
import pprint

import nipype.interfaces.fsl as fsl
fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

import nipype.pipeline.engine as pe

from macapype.pipelines.full_segment import create_full_segment_pnh_T1xT2
from macapype.utils.utils_tests import load_test_data
from macapype.utils.utils_spm import format_spm_priors

from macapype.utils.utils_bids import create_datasource

my_path = "/hpc/crise/meunier.d"


###############################################################################
def create_main_workflow(data_path, main_path, subject_ids, sessions,
                         acquisitions, template, priors, params_file):
    """
    create_main_workflow
    """

    # formating args
    data_path = op.abspath(data_path)

    if not op.isdir(main_path):
        os.makedirs(main_path)

    # params
    if params_file is not None:

        assert os.path.exists(params_file), "Error with file {}".format(
            params_file)

        params = json.load(open(params_file))
    else:
        params = {}

    print(params)
    pprint.pprint(params)

    # priors
    if template is None and priors is None:
        inia_dir = load_test_data("inia19", path_to=my_path)
        template = op.join(inia_dir, "inia19-t1-brain.nii")
        priors = [
            op.join(inia_dir, "inia19-prob_1.nii"),
            op.join(inia_dir, "inia19-prob_2.nii"),
            op.join(inia_dir, "inia19-prob_0.nii")
        ]

    # case priors are one single file with 3 tissue merged
    if len(priors) == 1:
        priors = priors[0]

    priors = format_spm_priors(priors, directory=main_path)

    # main_workflow
    main_workflow = pe.Workflow(name="T1xT2_processing_workflow_json")
    main_workflow.base_dir = main_path

    datasource = create_datasource(data_path, subject_ids, sessions,
                                   acquisitions)

    segment_pnh = create_full_segment_pnh_T1xT2(template, priors, params)

    main_workflow.connect(
        datasource, 'T1', segment_pnh, 'inputnode.T1')
    main_workflow.connect(
        datasource, 'T2', segment_pnh, 'inputnode.T2')

    return main_workflow


################################################################################
if __name__ == '__main__':
    # Command line parser
    parser = argparse.ArgumentParser(
        description="PNH segmentation pipeline from Regis Trapeau")
    parser.add_argument("-data", dest="data", type=str, required=True,
                        help="Directory containing MRI data (BIDS)")
    parser.add_argument("-out", dest="out", type=str,
                        help="Output directory", required=True)
    parser.add_argument("-ses", dest="ses", type=str, nargs='+',
                        help="Sessions ID")
    parser.add_argument("-acq", dest="acq", type=str, nargs='+',
                        help="Acquisitions ID")
    parser.add_argument("-subjects", dest="subjects", type=str, nargs='+',
                        help="Subjects' ID", required=False)
    parser.add_argument("-template", dest="template", type=str,
                        default=None, help="Anatomical template")
    parser.add_argument("-priors", dest="priors", type=str, nargs='+',
                        default=None, help="Tissues probability maps")
    parser.add_argument("-params", dest="params_file", type=str,
                        help="Parameters json file", required=False)

    args = parser.parse_args()

    # main_workflow
    print("Initialising the pipeline...")
    wf = create_main_workflow(
        data_path=args.data,
        main_path=args.out,
        subject_ids=args.subjects,
        sessions=args.ses,
        acquisitions=args.acq,
        template=args.template,
        priors=args.priors,
        params_file=args.params_file
    )
    # wf.write_graph(graph2use="colored")
    wf.config['execution'] = {'remove_unnecessary_outputs': 'false'}
    print('The PNH segmentation pipeline is ready')

    print("Start to process")
    wf.run()
    # wf.run(plugin='MultiProc', plugin_args={'n_procs' : 2})
