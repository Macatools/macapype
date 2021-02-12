#!/usr/bin/env python3
"""
    Non humain primates anatomical segmentation pipeline based ANTS

    Adapted in Nipype from an original pipelin of Kepkee Loh wrapped.

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

    -params
        json parameter file; leave blank if None

    Example
    ---------
    python segment_kepkee.py -data [PATH_TO_BIDS] -out ../local_tests/ -subjects Elouk

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
import json
import pprint

import nipype

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as niu

import nipype.interfaces.fsl as fsl
fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

from macapype.pipelines.full_pipelines import (
    create_full_spm_subpipes,
    create_full_ants_subpipes,
    create_full_T1_spm_subpipes,
    create_full_T1_ants_subpipes,)

from macapype.utils.utils_bids import (create_datasource_indiv_params,
                                       create_datasource)

from macapype.utils.utils_tests import load_test_data, format_template

from macapype.utils.utils_nodes import node_output_exists

from macapype.utils.misc import show_files, get_first_elem

###############################################################################

def create_main_workflow(data_dir, process_dir, soft, subjects, sessions,
<<<<<<< HEAD
                         acquisitions, records, params_file, indiv_params_file,
                         wf_name="test_pipeline_single", mask_file = None):
=======
                         acquisitions, reconstructions, params_file, indiv_params_file,
                         wf_name="test_pipeline_single"):
>>>>>>> 16d112a8e281c3c94fb1b3d336705f3df62b52d9
    """ Set up the segmentatiopn pipeline based on ANTS

    Arguments
    ---------
    data_path: pathlike str
        Path to the BIDS directory that contains anatomical images

    out_path: pathlike str
        Path to the ouput directory (will be created if not alredy existing).
        Previous outputs maybe overwritten.

    soft: str
        Indicate which analysis should be launched; so for, only spm and ants
        are accepted; can be extended

    subjects: list of str (optional)
        Subject's IDs to match to BIDS specification (sub-[SUB1], sub-[SUB2]...)

    sessions: list of str (optional)
        Session's IDs to match to BIDS specification (ses-[SES1], ses-[SES2]...)

    acquisitions: list of str (optional)
        Acquisition name to match to BIDS specification (acq-[ACQ1]...)

    indiv_params_file: path to a JSON file
        JSON file that specify some parameters of the pipeline,
        unique for the subjects/sessions.

    params_file: path to a JSON file
        JSON file that specify some parameters of the pipeline.


    Returns
    -------
    workflow: nipype.pipeline.engine.Workflow


    """

    # formating args
    data_dir = op.abspath(data_dir)

    if not op.isdir(process_dir):
        os.makedirs(process_dir)

    # params
    params = {}
    if params_file is not None:

        print("Params:", params_file)

        assert os.path.exists(params_file), "Error with file {}".format(
            params_file)

        params = json.load(open(params_file))

    pprint.pprint(params)

    # indiv_params
    indiv_params = {}
    if indiv_params_file is not None:

        print("Multi Params:", indiv_params_file)

        assert os.path.exists(indiv_params_file), "Error with file {}".format(
            indiv_params_file)

        indiv_params = json.load(open(indiv_params_file))

        wf_name+="_indiv_params"


    pprint.pprint(indiv_params)

    # params_template
    assert ("general" in params.keys() and \
        "template_name" in params["general"].keys()), \
            "Error, the params.json should contains a general/template_name"

    template_name = params["general"]["template_name"]

    if "general" in params.keys() and "my_path" in params["general"].keys():
        my_path = params["general"]["my_path"]
    else:
        my_path = ""

    nmt_dir = load_test_data(template_name, path_to = my_path)
    params_template = format_template(nmt_dir, template_name)
    print (params_template)

    # soft
    wf_name += "_{}".format(soft)

    if mask_file is not None:
         wf_name += "_mask"

    soft = soft.lower().split("_")
    assert "spm" in soft or "ants" in soft, \
        "error with {}, should be among [spm12, spm, ants]".format(soft)

    # main_workflow
    main_workflow = pe.Workflow(name= wf_name)
    main_workflow.base_dir = process_dir

    if "spm" in soft or "spm12" in soft:
        if "t1" in soft:
            segment_pnh = create_full_T1_spm_subpipes(
                params_template=params_template, params=params)
        else:
            segment_pnh = create_full_spm_subpipes(
                params_template=params_template, params=params)
    elif "ants" in soft:
        if "t1" in soft:
            segment_pnh = create_full_T1_ants_subpipes(
                params_template=params_template, params=params)
        else:
            segment_pnh = create_full_ants_subpipes(
                params_template=params_template, params=params,
                mask_file=mask_file)

    if indiv_params:
        datasource = create_datasource_indiv_params(data_dir, indiv_params,
                                                    subjects, sessions,
                                                    acquisitions,
                                                    reconstructions)

        main_workflow.connect(datasource, "indiv_params",
                              segment_pnh,'inputnode.indiv_params')
    else:
        datasource = create_datasource(data_dir, subjects, sessions,
                                       acquisitions, reconstructions)

    main_workflow.connect(datasource, 'T1', segment_pnh, 'inputnode.list_T1')

    if not "t1" in soft:
        main_workflow.connect(datasource, 'T2', 
                              segment_pnh, 'inputnode.list_T2')


    main_workflow.write_graph(graph2use="colored")
    main_workflow.config['execution'] = {'remove_unnecessary_outputs': 'false'}

    if not "test" in soft:
        if "seq" in soft:
            main_workflow.run()
        else:
            main_workflow.run(plugin='MultiProc', plugin_args={'n_procs' : 4})


if __name__ == '__main__':

    # Command line parser
    parser = argparse.ArgumentParser(
        description="PNH segmentation pipeline")

    parser.add_argument("-data", dest="data", type=str, required=True,
                        help="Directory containing MRI data (BIDS)")
    parser.add_argument("-out", dest="out", type=str, #nargs='+',
                        help="Output dir", required=True)
    parser.add_argument("-soft", dest="soft", type=str,
                        help="Sofware of analysis (SPM or ANTS are defined)",
                        required=True)
    parser.add_argument("-subjects", "-sub", dest="sub",
                        type=str, nargs='+', help="Subjects", required=False)
    parser.add_argument("-sessions", "-ses", dest="ses",
                        type=str, nargs='+', help="Sessions", required=False)
    parser.add_argument("-acquisitions", "-acq", dest="acq", type=str,
                        nargs='+', default=None, help="Acquisitions")
    parser.add_argument("-records", "-rec", dest="rec", type=str, nargs='+',
                        default=None, help="Records")
    parser.add_argument("-params", dest="params_file", type=str,
                        help="Parameters json file", required=False)
    parser.add_argument("-indiv_params", dest="indiv_params_file", type=str,
                        help="Individual parameters json file", required=False)
    parser.add_argument("-mask", dest="mask_file", type=str,
                        help="precomputed mask file", required=False)

    args = parser.parse_args()

    # main_workflow
    print("Initialising the pipeline...")
    create_main_workflow(
        data_dir=args.data,
        soft=args.soft,
        process_dir=args.out,
        subjects=args.sub,
        sessions=args.ses,
        acquisitions=args.acq,
        reconstructions=args.rec,
        params_file=args.params_file,
        indiv_params_file=args.indiv_params_file,
        mask_file=args.mask_file)

