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
    python segment_pnh_kepkee.py -data [PATH_TO_BIDS] -out ../local_tests/ -subjects Elouk

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
    create_full_segment_pnh_subpipes, create_full_T1xT2_segment_pnh_subpipes)

from macapype.utils.utils_bids import (create_datasource_multi_params,
                                       create_datasource)

from macapype.utils.utils_tests import load_test_data, format_template

from macapype.utils.utils_nodes import node_output_exists

from macapype.utils.misc import show_files, get_first_elem

###############################################################################

def create_main_workflow(data_dir, process_dir, soft, subjects, sessions,
                         acquisitions, params_file, multi_params_file,
                         wf_name="baboon_preprocessed"):
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

    multi_params_file: path to a JSON file
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

    # multi_params
    multi_params = {}
    if multi_params_file is not None:

        print("Multi Params:", multi_params_file)

        assert os.path.exists(multi_params_file), "Error with file {}".format(
            multi_params_file)

        multi_params = json.load(open(multi_params_file))

        wf_name+="_multi_params"


    pprint.pprint(multi_params)

    # params_template
    if "general" in params.keys() and "my_path" in params["general"].keys():
        my_path = params["general"]["my_path"]
    else:
        my_path = ""

    if "general" in params.keys() and "template_name" in params["general"].keys():
        template_name = params["general"]["template_name"]
    else:
        template_name = 'baboon_template'

    #nmt_dir = load_test_data(template_name, path_to = my_path)
    #params_template = format_template(nmt_dir, template_name)
    #print (params_template)

    # specify own template
    params_template = {
        "template_head": "/hpc/meca/users/loh.k/baboon_proc/haiko89_template/Haiko89_Asymmetric.Template_n89.nii.gz",
        "template_brain": "/hpc/meca/users/loh.k/baboon_proc/haiko89_template/Haiko89_Asymmetric.Template_n89.nii.gz",
        "template_gm": "/hpc/meca/users/loh.k/baboon_proc/haiko89_template/TPM_Asymmetric.GreyMatter_Haiko89.nii.gz",
        "template_wm": "/hpc/meca/users/loh.k/baboon_proc/haiko89_template/TPM_Asymmetric.WhiteMatter_Haiko89.nii.gz",
        "template_csf": "/hpc/meca/users/loh.k/baboon_proc/haiko89_template/TPM_Asymmetric.CSF_Haiko89.nii.gz"
    }    

    print (params_template)

    # soft
    soft = soft.lower()
    assert soft in ["spm12", "spm", "ants"], \
        "error with {}, should be among [spm12, spm, ants]".format(soft)
    wf_name += "_{}".format(soft)

    # main_workflow
    main_workflow = pe.Workflow(name="baboon_preprocessed")
    #main_workflow = pe.Workflow(name=wf_name)
    main_workflow.base_dir = process_dir


    if soft in ["spm","spm12"]:
        segment_pnh = create_full_T1xT2_segment_pnh_subpipes(
            params_template=params_template, params=params)

    elif soft=="ants":
        segment_pnh = create_full_segment_pnh_subpipes(
            params_template=params_template, params=params)


    if multi_params:
        datasource = create_datasource_multi_params(data_dir, multi_params,
                                                    subjects, sessions)

        main_workflow.connect(datasource, "indiv_params",
                              segment_pnh,'inputnode.indiv_params')
    else:
        datasource = create_datasource(data_dir, subjects, sessions,
                                       acquisitions)

    main_workflow.connect(datasource, 'T1', segment_pnh, 'inputnode.T1')
    main_workflow.connect(datasource, 'T2', segment_pnh, 'inputnode.T2')

    return main_workflow

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
    parser.add_argument("-subjects", dest="subjects", type=str, nargs='+',
                        help="Subjects' ID", required=False)
    parser.add_argument("-ses", dest="ses", type=str,
                        help="Session", required=False)
    parser.add_argument("-acq", dest="acq", type=str, nargs='+', default=None,
                        help="Acquisitions ID")
    parser.add_argument("-params", dest="params_file", type=str,
                        help="Parameters json file", required=False)
    parser.add_argument("-multi_params", dest="multi_params_file", type=str,
                        help="Multiple Parameters json file", required=False)


    args = parser.parse_args()

    # main_workflow
    print("Initialising the pipeline...")
    wf = create_main_workflow(
        data_dir=args.data,
        soft=args.soft,
        process_dir=args.out,
        subjects=args.subjects,
        sessions=args.ses,
        acquisitions=args.acq,
        params_file=args.params_file,
        multi_params_file=args.multi_params_file)

    wf.write_graph(graph2use="colored")
    wf.config['execution'] = {'remove_unnecessary_outputs': 'false'}
    #print('The PNH segmentation pipeline is ready')
    #print("Start to process")
    wf.run()
