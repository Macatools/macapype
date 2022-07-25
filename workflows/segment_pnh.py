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
    python segment_pnh.py -data [PATH_TO_BIDS] -out ../local_tests/ -subjects Elouk

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
    create_full_T1_ants_subpipes,
    create_transfo_FLAIR_pipe,
    create_transfo_MD_pipe)

from macapype.utils.utils_bids import (create_datasource, create_datasource_indiv_params,
                                       create_datasink)

from macapype.utils.utils_tests import load_test_data, format_template

from macapype.utils.utils_nodes import node_output_exists
from macapype.utils.utils_params import update_params

from macapype.utils.misc import show_files, get_first_elem, parse_key

###############################################################################

def create_main_workflow(data_dir, process_dir, soft, species, subjects, sessions,
                         acquisitions, reconstructions, params_file,
                         indiv_params_file, mask_file, template_path,
                         template_files, nprocs, wf_name="macapype",
                         deriv=False, pad=False):

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

    soft = soft.lower()

    ssoft = soft.split("_")

    new_ssoft = ssoft.copy()

    if 'test' in ssoft:
        new_ssoft.remove('test')

    if 'prep' in ssoft:
        new_ssoft.remove('prep')

    if 't1' in ssoft:
        new_ssoft.remove('t1')

    if 'native' in ssoft:
        new_ssoft.remove('native')

    if 'template' in ssoft:
        new_ssoft.remove('template')


    soft = "_".join(new_ssoft)

    # formating args
    data_dir = op.abspath(data_dir)


    try:
        os.makedirs(process_dir)
    except OSError:
        print("process_dir {} already exists".format(process_dir))

    #params
    if params_file is None:

        # species
        if species is not None:

            species = species.lower()

            rep_species = {"marmoset":"marmo", "marmouset":"marmo", "chimpanzee":"chimp"}

            if species in list(rep_species.keys()):
                species = rep_species[species]

            list_species = ["macaque", "marmo", "baboon", "chimp"]

            assert species in list_species, \
                "Error, species {} should in the following list {}".format(
                    species, list_species)

            package_directory = op.dirname(op.abspath(__file__))

            params_file = "{}/params_segment_{}_{}.json".format(
                package_directory, species, soft)

        else:
            print("Error, no -params or no -species was found (one or the \
                other is mandatory)")
            exit(-1)

    print("Params:", params_file)

    params, indiv_params, extra_wf_name = update_params(ssoft=ssoft, subjects=subjects, sessions=sessions,
                           params_file=params_file, indiv_params_file=indiv_params_file)

    wf_name += extra_wf_name

    # soft
    wf_name += "_{}".format(soft)

    if 't1' in ssoft:
        wf_name += "_t1"

    if mask_file is not None:
        wf_name += "_mask"

    assert "spm" in ssoft or "spm12" in ssoft or "ants" in ssoft, \
        "error with {}, should be among [spm12, spm, ants]".format(ssoft)

    # params_template
    if template_path is not None:
        print(template_files)

        params_template = {}

        assert len(template_files) > 1, "Error, template_files unspecified {}".format(template_files)

        template_head = os.path.join(template_path,template_files[0])
        assert os.path.exists(template_head), "Could not find template_head {}".format(template_head)
        params_template["template_head"] = template_head

        template_brain = os.path.join(template_path,template_files[1])
        assert os.path.exists(template_brain), "Could not find template_brain {}".format(template_brain)
        params_template["template_brain"] = template_brain

        if len(template_files) == 3:

            template_seg = os.path.join(template_path,template_files[2])
            assert os.path.exists(template_seg), "Could not find template_seg {}".format(template_seg)
            params_template["template_seg"] = template_seg

        elif len(template_files) == 5:

            template_gm = os.path.join(template_path,template_files[2])
            assert os.path.exists(template_gm), "Could not find template_gm {}".format(template_gm)
            params_template["template_gm"] = template_gm

            template_wm = os.path.join(template_path,template_files[3])
            assert os.path.exists(template_wm), "Could not find template_wm {}".format(template_wm)
            params_template["template_wm"] = template_wm

            template_csf = os.path.join(template_path,template_files[4])
            assert os.path.exists(template_csf), "Could not find template_csf {}".format(template_csf)
            params_template["template_csf"] = template_csf

        else:
            print("Unknown template_files format, should be 3 or 5 files")
            exit(-1)

    else:
        ### use template from params
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

    # main_workflow
    main_workflow = pe.Workflow(name= wf_name)

    main_workflow.base_dir = process_dir

    # which soft is used
    if "spm" in ssoft or "spm12" in ssoft:
        if 'native' in ssoft:
            space='native'
        else:
            space='template'

        segment_pnh_pipe = create_full_spm_subpipes(
            params_template=params_template, params=params, pad=pad,
            space=space)

    elif "ants" in ssoft:
        if "template" in ssoft:
            space="template"
        else:
            space="native"

        if "t1" in ssoft:
            segment_pnh_pipe = create_full_T1_ants_subpipes(
                params_template=params_template, params=params, space=space,
                pad=pad)
        else:
            segment_pnh_pipe = create_full_ants_subpipes(
                params_template=params_template, params=params,
                mask_file=mask_file, space=space, pad=pad)

    # list of all required outputs
    output_query = {}

    # T1 (mandatory, always added)
    # T2 is optional, if "_T1" is added in the -soft arg
    if 't1' in ssoft:
        output_query['T1'] = {
            "datatype": "anat", "suffix": "T1w",
            "extension": ["nii", ".nii.gz"]}

    else:
        output_query['T1'] = {
            "datatype": "anat", "suffix": "T1w",
            "extension": ["nii", ".nii.gz"]}

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


        if "transfo_FLAIR_pipe" in params.keys():
            print("Found transfo_FLAIR_pipe")

        transfo_FLAIR_pipe = create_transfo_FLAIR_pipe(params=parse_key(params, "transfo_FLAIR_pipe"),
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

        if "transfo_MD_pipe" in params.keys():
            print("Found transfo_MD_pipe")

        transfo_MD_pipe = create_transfo_MD_pipe(params=parse_key(params, "transfo_MD_pipe"),
                                                 params_template=params_template)

        main_workflow.connect(segment_pnh_pipe,
                                "old_segment_pipe.outputnode.threshold_wm",
                                transfo_MD_pipe, 'inputnode.threshold_wm')

        main_workflow.connect(datasource, ('MD', get_first_elem),
                                transfo_MD_pipe, 'inputnode.MD')

        main_workflow.connect(datasource, ('b0mean', get_first_elem),
                                transfo_MD_pipe, 'inputnode.b0mean')

        main_workflow.connect(segment_pnh_pipe, "debias.t1_debiased_file",
                            transfo_MD_pipe, 'inputnode.orig_T1')

        main_workflow.connect(segment_pnh_pipe, "debias.t2_debiased_brain_file",
                            transfo_MD_pipe, 'inputnode.SS_T2')

        main_workflow.connect(segment_pnh_pipe, "reg.transfo_file",
                            transfo_MD_pipe, 'inputnode.lin_transfo_file')

        main_workflow.connect(segment_pnh_pipe, "reg.inv_transfo_file",
                            transfo_MD_pipe, 'inputnode.inv_lin_transfo_file')

    if deriv:

        datasink_name = os.path.join("derivatives", wf_name)

        if "regex_subs" in params.keys():
            params_regex_subs = params["regex_subs"]
        else:
            params_regex_subs={}

        if "subs" in params.keys():
            params_subs = params["rsubs"]
        else:
            params_subs={}

        print (datasource.iterables)

        datasink = create_datasink(iterables=datasource.iterables,
                                   name=datasink_name,
                                   params_subs=params_subs,
                                   params_regex_subs=params_regex_subs)

        datasink.inputs.base_directory = process_dir

        if "brain_extraction_pipe" in params.keys():

            ### rename brain_mask
            rename_brain_mask = pe.Node(niu.Rename(), name = "rename_brain_mask")
            rename_brain_mask.inputs.format_string = "sub-%(sub)s_ses-%(ses)s_space-native_desc-brain_mask"
            rename_brain_mask.inputs.parse_string = r"sub-(?P<sub>\w*)_ses-(?P<ses>\w*)_.*"
            rename_brain_mask.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.brain_mask',
                rename_brain_mask, 'in_file')

            main_workflow.connect(
                rename_brain_mask, 'out_file',
                datasink, '@brain_mask')

        if "brain_segment_pipe" in params.keys():

            ### rename debiased_brain
            rename_debiased_brain = pe.Node(niu.Rename(), name = "rename_debiased_brain")
            rename_debiased_brain.inputs.format_string = "sub-%(sub)s_ses-%(ses)s_space-native_desc-debiased_desc-brain_T1w"
            rename_debiased_brain.inputs.parse_string = r"sub-(?P<sub>\w*)_ses-(?P<ses>\w*)_.*"
            rename_debiased_brain.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.debiased_brain',
                rename_debiased_brain, 'in_file')

            main_workflow.connect(
                rename_debiased_brain, 'out_file',
                datasink, '@debiased_brain')

            ### rename debiased_T1
            rename_debiased_T1 = pe.Node(niu.Rename(), name = "rename_debiased_T1")
            rename_debiased_T1.inputs.format_string = "sub-%(sub)s_ses-%(ses)s_space-native_desc-debiased_T1w"
            rename_debiased_T1.inputs.parse_string = r"sub-(?P<sub>\w*)_ses-(?P<ses>\w*)_.*"
            rename_debiased_T1.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.debiased_T1',
                rename_debiased_T1, 'in_file')

            main_workflow.connect(
                rename_debiased_T1, 'out_file',
                datasink, '@debiased_T1')

            ### rename segmented_brain_mask
            rename_segmented_brain_mask = pe.Node(niu.Rename(), name = "rename_segmented_brain_mask")
            rename_segmented_brain_mask.inputs.format_string = "sub-%(sub)s_ses-%(ses)s_space-native_desc-brain_dseg"
            rename_segmented_brain_mask.inputs.parse_string = r"sub-(?P<sub>\w*)_ses-(?P<ses>\w*)_.*"
            rename_segmented_brain_mask.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.segmented_brain_mask',
                rename_segmented_brain_mask, 'in_file')

            main_workflow.connect(
                rename_segmented_brain_mask, 'out_file',
                datasink, '@segmented_brain_mask')

            ### rename prob_wm
            print("Renaming prob_wm file")
            rename_prob_wm = pe.Node(niu.Rename(), name = "rename_prob_wm")
            rename_prob_wm.inputs.format_string = "sub-%(sub)s_ses-%(ses)s_space-{}_label-WM_probseg".format(space)
            rename_prob_wm.inputs.parse_string = r"sub-(?P<sub>\w*)_ses-(?P<ses>\w*)_.*"
            rename_prob_wm.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.prob_wm',
                rename_prob_wm, 'in_file')

            main_workflow.connect(
                rename_prob_wm, ('out_file', show_files),
                datasink, '@prob_wm')

            ### rename prob_gm
            print("Renaming prob_gm file")
            rename_prob_gm = pe.Node(niu.Rename(), name = "rename_prob_gm")
            rename_prob_gm.inputs.format_string = "sub-%(sub)s_ses-%(ses)s_space-{}_label-GM_probseg".format(space)
            rename_prob_gm.inputs.parse_string = r"sub-(?P<sub>\w*)_ses-(?P<ses>\w*)_.*"
            rename_prob_gm.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.prob_gm',
                rename_prob_gm, 'in_file')

            main_workflow.connect(
                rename_prob_gm, ('out_file', show_files),
                datasink, '@prob_gm')

            ### rename prob_csf
            print("Renaming prob_csf file")
            rename_prob_csf = pe.Node(niu.Rename(), name = "rename_prob_csf")
            rename_prob_csf.inputs.format_string = "sub-%(sub)s_ses-%(ses)s_space-{}_label-CSF_probseg".format(space)
            rename_prob_csf.inputs.parse_string = r"sub-(?P<sub>\w*)_ses-(?P<ses>\w*)_.*"
            rename_prob_csf.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.prob_csf',
                rename_prob_csf, 'in_file')

            main_workflow.connect(
                rename_prob_csf, ('out_file', show_files),
                datasink, '@prob_csf')

            # rename 5tt
            if "export_5tt_pipe" in params["brain_segment_pipe"]:
                print("Renaming 5tt file")

                rename_gen_5tt = pe.Node(niu.Rename(), name = "rename_gen_5tt")
                rename_gen_5tt.inputs.format_string = "sub-%(sub)s_ses-%(ses)s_space-{}_desc-5tt_dseg".format(space)
                rename_gen_5tt.inputs.parse_string = r"sub-(?P<sub>\w*)_ses-(?P<ses>\w*)_.*"
                rename_gen_5tt.inputs.keep_ext = True

                main_workflow.connect(
                    segment_pnh_pipe, 'outputnode.gen_5tt',
                    rename_gen_5tt, 'in_file')

                main_workflow.connect(
                    rename_gen_5tt, 'out_file',
                    datasink, '@gen_5tt')

        if 'flair' in ssoft :

            main_workflow.connect(
                transfo_FLAIR_pipe, 'outputnode.norm_FLAIR',
                datasink, '@norm_flair')

    main_workflow.write_graph(graph2use="colored")
    main_workflow.config['execution'] = {'remove_unnecessary_outputs': 'false'}

    # saving real params.json
    real_params_file = op.join(process_dir, wf_name, "real_params.json")
    with open(real_params_file, 'w+') as fp:
        json.dump(params, fp)

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
    parser.add_argument("-species", dest="species", type=str,
                        help="Type of PNH to process",
                        required=False)
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

    parser.add_argument("-template_path", dest="template_path", type=str,
                        help="specifies user-based template path",
                        required=False)

    parser.add_argument("-template_files", dest="template_files", type=str,
                        nargs="+", help="specifies user-based template files \
                            (3 or 5 are possible options)",
                        required=False)

    parser.add_argument("-nprocs", dest="nprocs", type=int,
                        help="number of processes to allocate", required=False)

    parser.add_argument("-deriv", dest="deriv", action='store_true',
                        help="output derivatives in BIDS orig directory",
                        required=False)

    parser.add_argument("-pad", dest="pad", action='store_true',
                        help="padding mask and seg_mask",
                        required=False)


    args = parser.parse_args()

    # main_workflow
    print("Initialising the pipeline...")
    create_main_workflow(
        data_dir=args.data,
        soft=args.soft,
        process_dir=args.out,
        species=args.species,
        subjects=args.sub,
        sessions=args.ses,
        acquisitions=args.acq,
        reconstructions=args.rec,
        params_file=args.params_file,
        indiv_params_file=args.indiv_params_file,
        mask_file=args.mask_file,
        template_path=args.template_path,
        template_files=args.template_files,
        nprocs=args.nprocs,
        deriv=args.deriv,
        pad=args.pad)

if __name__ == '__main__':
    main()
