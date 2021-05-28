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
    create_full_native_spm_subpipes,
    create_full_ants_subpipes,
    create_full_T1_ants_subpipes,
    create_transfo_FLAIR_pipe,
    create_transfo_MD_pipe)

from macapype.utils.utils_bids import (create_datasource_indiv_params,
                                       create_datasource,
                                       create_datasink)

from macapype.utils.utils_tests import load_test_data, format_template

from macapype.utils.utils_nodes import node_output_exists

from macapype.utils.misc import show_files, get_first_elem

###############################################################################

def create_main_workflow(data_dir, process_dir, soft, subjects, sessions,
                         acquisitions, reconstructions, params_file,
                         indiv_params_file, mask_file, nprocs,
                         wf_name="test_pipeline_single",
                         deriv=True):

    # macapype_pipeline
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

        print("Indiv Params:", indiv_params_file)

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

    ssoft = soft.lower().split("_")

    assert "spm" in ssoft or "spm12" in ssoft or "ants" in ssoft, \
        "error with {}, should be among [spm12, spm, ants]".format(ssoft)

    # main_workflow
    main_workflow = pe.Workflow(name= wf_name)

    main_workflow.base_dir = process_dir

    if "spm" in ssoft or "spm12" in ssoft:
        if 'native' in ssoft:
            segment_pnh_pipe = create_full_native_spm_subpipes(
                params_template=params_template, params=params)
        else:
            segment_pnh_pipe = create_full_spm_subpipes(
                params_template=params_template, params=params)

    elif "ants" in ssoft:
        if "t1" in ssoft:
            segment_pnh_pipe = create_full_T1_ants_subpipes(
                params_template=params_template, params=params)
        else:
            segment_pnh_pipe = create_full_ants_subpipes(
                params_template=params_template, params=params,
                mask_file=mask_file)

    # list of all required outputs
    output_query = {}

    # T1 (mandatory, always added)
    output_query['T1'] = {
            "datatype": "anat", "suffix": "T1w",
            "extension": ["nii", ".nii.gz"]
        }

    # T2 is optional, if "_T1" is added in the -soft arg
    if not 't1' in ssoft:
        output_query['T2'] = {
            "datatype": "anat", "suffix": "T2w",
            "extension": ["nii", ".nii.gz"]}

    # FLAIR is optional, if "_FLAIR" is added in the -soft arg
    if 'flair' in ssoft:
        output_query['FLAIR'] = {
            "datatype": "anat", "suffix": "FLAIR",
            "extension": ["nii", ".nii.gz"]}

    # MD and b0mean are optional, if "_MD" is added in the -soft arg
    if 'md' in ssoft:
        output_query['MD'] =  {
            "datatype": "dwi", "acquisition": "MD", "suffix": "dwi",
            "extension": ["nii", ".nii.gz"]}

        output_query['b0mean'] = {
            "datatype": "dwi", "acquisition": "b0mean", "suffix": "dwi",
            "extension": ["nii", ".nii.gz"]}

    # indiv_params
    if indiv_params:
        datasource = create_datasource_indiv_params(
            output_query, data_dir, indiv_params, subjects, sessions,
            acquisitions, reconstructions)

        main_workflow.connect(datasource, "indiv_params",
                              segment_pnh_pipe,'inputnode.indiv_params')
    else:
        datasource = create_datasource(
            output_query, data_dir, subjects,  sessions, acquisitions,
            reconstructions)

    main_workflow.connect(datasource, 'T1',
                          segment_pnh_pipe, 'inputnode.list_T1')

    if not "t1" in ssoft:
        main_workflow.connect(datasource, 'T2', 
                              segment_pnh_pipe, 'inputnode.list_T2')
    elif "t1" in ssoft and "spm" in ssoft:
        # cheating using T2 as T1
        main_workflow.connect(datasource, 'T1',
                              segment_pnh_pipe, 'inputnode.list_T2')

    if "flair" in ssoft:

        transfo_FLAIR_pipe = create_transfo_FLAIR_pipe(params=params,
                                        params_template=params_template)

        if "t1" in ssoft:
            main_workflow.connect(segment_pnh_pipe, "short_preparation_pipe.outputnode.preproc_T1",
                                transfo_FLAIR_pipe, 'inputnode.orig_T1')

        else:
            main_workflow.connect(segment_pnh_pipe, "debias.t1_debiased_file",
                                transfo_FLAIR_pipe, 'inputnode.orig_T1')


        main_workflow.connect(segment_pnh_pipe, "reg.transfo_file",
                              transfo_FLAIR_pipe, 'inputnode.lin_transfo_file')

        main_workflow.connect(datasource, ('FLAIR', get_first_elem),
                              transfo_FLAIR_pipe, 'inputnode.FLAIR')

    if 'md' in ssoft:

        transfo_MD_pipe = create_transfo_MD_pipe(params=params,
                                        params_template=params_template)

        main_workflow.connect(segment_pnh_pipe,
                                "old_segment_pipe.outputnode.threshold_wm",
                                transfo_MD_pipe, 'inputnode.threshold_wm')

        main_workflow.connect(datasource, ('MD', get_first_elem),
                                transfo_MD_pipe, 'inputnode.MD')

        main_workflow.connect(datasource, ('b0mean', get_first_elem),
                                transfo_MD_pipe, 'inputnode.b0mean')

        main_workflow.connect(segment_pnh_pipe, "debias.t1_debiased_file",
                            transfo_MD_pipe, 'inputnode.SS_T1')

        main_workflow.connect(segment_pnh_pipe, "debias.t1_debiased_brain_file",
                            transfo_MD_pipe, 'inputnode.orig_T1')

        main_workflow.connect(segment_pnh_pipe, "reg.transfo_file",
                            transfo_MD_pipe, 'inputnode.lin_transfo_file')

        main_workflow.connect(segment_pnh_pipe, "reg.inv_transfo_file",
                            transfo_MD_pipe, 'inputnode.inv_lin_transfo_file')

    if deriv:

        datasink_name = os.path.join("derivatives", "macapype_{}".format(soft))

        if "regex_subs" in params.values():
            params_regex_subs = params["regex_subs"]
        else:
            params_regex_subs={}


        if "subs" in params.values():
            params_subs = params["rsubs"]
        else:
            params_subs={}

        datasink = create_datasink(iterables=datasource.iterables,
                                   name=datasink_name,
                                   params_subs=params_subs,
                                   params_regex_subs=params_regex_subs)

        datasink.inputs.base_directory = process_dir

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.segmented_brain_mask',
            datasink, '@segmented_brain_mask')

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.brain_mask',
            datasink, '@brain_mask')

        if 'spm' in ssoft and not 'native' in ssoft:

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.norm_T1',
                datasink, '@norm_T1')

        if 'flair' in ssoft :

            main_workflow.connect(
                transfo_FLAIR_pipe, 'outputnode.norm_FLAIR',
                datasink, '@norm_flair')

    main_workflow.write_graph(graph2use="colored")
    main_workflow.config['execution'] = {'remove_unnecessary_outputs': 'false'}

    if nprocs is None:
        nprocs = 4

    if not "test" in ssoft:
        if "seq" in ssoft or nprocs==0:
            main_workflow.run()
        else:
            main_workflow.run(plugin='MultiProc',
                              plugin_args={'n_procs' : nprocs})
def main():

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
    parser.add_argument("-indiv_params", "-indiv", dest="indiv_params_file",
                        type=str, help="Individual parameters json file",
                        required=False)
    parser.add_argument("-mask", dest="mask_file", type=str,
                        help="precomputed mask file", required=False)
    parser.add_argument("-nprocs", dest="nprocs", type=int,
                        help="number of processes to allocate", required=False)
    parser.add_argument("-deriv", dest="deriv", action='store_true',
                        help="output derivatives in BIDS orig directory",
                        required=False)

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
        mask_file=args.mask_file,
        nprocs=args.nprocs,
        deriv=args.deriv)

if __name__ == '__main__':
    main()
