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

import sys
import os
import os.path as op

import argparse
import json
import pprint

import nipype

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as niu

import nipype.interfaces.fsl as fsl

from macapype.pipelines.full_pipelines import (
    create_full_T1T2_subpipes,
    create_full_T1_subpipes)

from macapype.pipelines.rename import rename_all_brain_derivatives

from macapype.utils.utils_bids import (create_datasource,
                                       create_datasource_indiv_params,
                                       create_datasink)

from macapype.utils.utils_tests import load_test_data, format_template

from macapype.utils.utils_params import update_params

from macapype.utils.misc import show_files, get_first_elem, parse_key

from macapype._version import __version__

fsl.FSLCommand.set_default_output_type('NIFTI_GZ')
###############################################################################


def create_main_workflow(cmd, data_dir, process_dir, soft, species, datatypes,
                         subjects, sessions, acquisitions, reconstructions,
                         params_file, indiv_params_file, mask_file,
                         template_path, template_files, nprocs, reorient,
                         deriv, pad, wf_name="macapype"):

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

    reconstructions: list of str (optional)
        Reconstructions name to match to BIDS specification (rec-[ACQ1]...)

    indiv_params_file: path to a JSON file
        JSON file that specify some parameters of the pipeline,
        unique for the subjects/sessions.

    params_file: path to a JSON file
        JSON file that specify some parameters of the pipeline.

    nprocs: integer
        number of processes that will be launched by MultiProc


    Returns
    -------
    workflow: nipype.pipeline.engine.Workflow


    """
    datatypes = [dt.lower() for dt in datatypes]

    soft = soft.lower()

    ssoft = soft.split("_")

    new_ssoft = ssoft.copy()

    if 'test' in ssoft:
        new_ssoft.remove('test')

    if 'prep' in ssoft:
        new_ssoft.remove('prep')

    if 'noseg' in ssoft:
        new_ssoft.remove('noseg')

    if 'native' in ssoft:
        new_ssoft.remove('native')

    if 'template' in ssoft:
        new_ssoft.remove('template')

    if 'robustreg' in ssoft:
        new_ssoft.remove('robustreg')

    soft = "_".join(new_ssoft)

    # formating args
    data_dir = op.abspath(data_dir)

    process_dir = op.abspath(process_dir)

    try:
        os.makedirs(process_dir)

    except OSError:
        print("process_dir {} already exists".format(process_dir))

    # params
    if params_file is None:

        # species
        if species is not None:

            species = species.lower()

            rep_species = {"marmoset": "marmo",
                           "marmouset": "marmo",
                           "chimpanzee": "chimp"}

            if species in list(rep_species.keys()):
                species = rep_species[species]

            list_species = ["macaque", "marmo", "baboon", "chimp", "human"]

            ok_species = False
            for cur_species in list_species:
                if species.startswith(cur_species):
                    ok_species = True

            if ok_species is False:
                print(f"Error, species {species} not in list")
                exit(-1)

            package_directory = op.dirname(op.abspath(__file__))

            params_file = "{}/params_segment_{}_{}.json".format(
                package_directory, species, soft)

        else:
            print("Error, no -params or no -species was found (one or the \
                other is mandatory)")
            exit(-1)

        print("Using default params file:", params_file)

    else:

        # format for relative path
        params_file = op.abspath(params_file)

        # params
        assert op.exists(params_file), "Error with file {}".format(
            params_file)

        print("Using orig params file:", params_file)

        wf_name += "_params"

    # indiv_params
    if indiv_params_file is not None:

        # format for relative path
        indiv_params_file = op.abspath(indiv_params_file)

        assert op.exists(indiv_params_file), "Error with file {}".format(
            indiv_params_file)

    params, indiv_params, extra_wf_name = update_params(
        ssoft=ssoft, subjects=subjects, sessions=sessions,
        params_file=params_file, indiv_params_file=indiv_params_file)

    # modifying if reorient
    if reorient is not None:
        print("reorient: ", reorient)

        if "short_preparation_pipe" in params.keys():
            params["short_preparation_pipe"]["avg_reorient_pipe"] = {
                "reorient":
                    {"origin": reorient, "deoblique": True}}

    wf_name += extra_wf_name

    # soft
    wf_name += "_{}".format(soft)

    if 't1' in datatypes:
        wf_name += '_t1'

        if 't2' in datatypes:
            wf_name += 't2'

    assert "spm" in ssoft or "spm12" in ssoft or "ants" in ssoft, \
        "error with {}, should be among [spm12, spm, ants]".format(ssoft)

    # adding forced space
    if "template" in ssoft:
        wf_name += "_template"

    # params_template
    if template_path is not None:

        # format for relative path
        template_path = op.abspath(template_path)

        assert os.path.exists(template_path), \
            "Error, template_path {} do not exists".format(template_path)

        print(template_files)

        params_template = {}

        assert len(template_files) > 1, \
            "Error, template_files unspecified {}".format(template_files)

        template_head = os.path.join(template_path, template_files[0])
        assert os.path.exists(template_head), \
            "Could not find template_head {}".format(template_head)
        params_template["template_head"] = template_head

        template_brain = os.path.join(template_path, template_files[1])
        assert os.path.exists(template_brain), \
            "Could not find template_brain {}".format(template_brain)
        params_template["template_brain"] = template_brain

        if len(template_files) == 2:

            print("Only two files (template_head and template_brain) have \
                been specified, segmentation will be without priors")

            if "brain_segment_pipe" in params.keys():
                pbs = params["brain_segment_pipe"]
                if "segment_atropos_pipe" in pbs.keys():
                    if "use_priors" in pbs["segment_atropos_pipe"].keys():
                        del pbs["segment_atropos_pipe"]["use_priors"]

        elif len(template_files) == 3:

            template_seg = os.path.join(template_path, template_files[2])
            assert os.path.exists(template_seg), \
                "Could not find template_seg {}".format(template_seg)
            params_template["template_seg"] = template_seg

        elif len(template_files) == 5:

            template_gm = os.path.join(template_path, template_files[2])
            assert os.path.exists(template_gm), \
                "Could not find template_gm {}".format(template_gm)
            params_template["template_gm"] = template_gm

            template_wm = os.path.join(template_path, template_files[3])
            assert os.path.exists(template_wm), \
                "Could not find template_wm {}".format(template_wm)
            params_template["template_wm"] = template_wm

            template_csf = os.path.join(template_path, template_files[4])
            assert os.path.exists(template_csf), \
                "Could not find template_csf {}".format(template_csf)
            params_template["template_csf"] = template_csf

        else:
            print("Unknown template_files format, should be 3 or 5 files")
            exit(-1)

        params_template_stereo = params_template
        params_template_brainmask = params_template
        params_template_seg = params_template

    else:
        # use template from params
        assert "general" in params.keys(), \
            "Error, the params.json should contains a general section"

        pg = params["general"]

        if "my_path" in pg.keys():
            my_path = pg["my_path"]
        else:
            my_path = ""

        # template_name
        if "template_name" in pg.keys():

            template_name = pg["template_name"]

            template_dir = load_test_data(template_name, path_to=my_path)
            params_template = format_template(template_dir, template_name)
        else:
            params_template = {}

        # template_stereo_name
        if "template_stereo_name" in pg.keys():

            template_stereo_name = pg["template_stereo_name"]
            print("template_stereo_name = {}".format(template_stereo_name))
            template_stereo_dir = load_test_data(template_stereo_name,
                                                 path_to=my_path)
            params_template_stereo = format_template(template_stereo_dir,
                                                     template_stereo_name)

        else:
            if not params_template:
                print("Error, either template_name or \
                    template_stereo_name should be defined")

            params_template_stereo = params_template

        # template_brainmask_name
        if "template_brainmask_name" in pg.keys():
            template_brainmask_name = pg["template_brainmask_name"]
            print("template_brainmask_name = {}".format(
                template_brainmask_name))
            template_brainmask_dir = load_test_data(
                template_brainmask_name,  path_to=my_path)
            params_template_brainmask = format_template(
                template_brainmask_dir, template_brainmask_name)

        else:
            if not params_template:
                print("Error, either template_name or \
                    template_brainmask_name should be defined")

            params_template_brainmask = params_template

        # template_seg_name
        if "template_seg_name" in pg.keys():

            template_seg_name = pg["template_seg_name"]
            print("template_seg_name = {}".format(template_seg_name))
            template_seg_dir = load_test_data(
                template_seg_name, path_to=my_path)
            params_template_seg = format_template(
                template_seg_dir, template_seg_name)

        else:
            if not params_template:
                print("Error, either template_name or \
                    template_seg_name should be defined")

            params_template_seg = params_template

    # main_workflow
    main_workflow = pe.Workflow(name=wf_name)

    main_workflow.base_dir = process_dir

    # by default, space of segmentation is native, except if
    if "template" in ssoft:
        space = "template"

    else:
        space = "native"

    # which soft is used
    if 't1' in datatypes and 't2' in datatypes:
        segment_pnh_pipe = create_full_T1T2_subpipes(
            params_template_stereo=params_template_stereo,
            params_template_brainmask=params_template_brainmask,
            params_template_seg=params_template_seg,
            params=params, mask_file=mask_file, space=space, pad=pad)

    elif 't1' in datatypes:
        segment_pnh_pipe = create_full_T1_subpipes(
            params_template_stereo=params_template_stereo,
            params_template_brainmask=params_template_brainmask,
            params_template_seg=params_template_seg,
            params=params, mask_file=mask_file, space=space, pad=pad)

    # list of all required outputs
    output_query = {}

    # T1 (mandatory, always added)
    # T2 is optional, if "_T1" is added in the -soft arg
    if 't1' in datatypes:
        output_query['T1'] = {
            "datatype": "anat", "suffix": "T1w",
            "extension": ["nii", ".nii.gz"]}

    if 't2' in datatypes:
        output_query['T2'] = {
            "datatype": "anat", "suffix": "T2w",
            "extension": ["nii", ".nii.gz"]}

    # indiv_params
    if indiv_params:
        datasource = create_datasource_indiv_params(
            output_query, data_dir, indiv_params, subjects, sessions,
            acquisitions, reconstructions)

        main_workflow.connect(datasource, "indiv_params",
                              segment_pnh_pipe, 'inputnode.indiv_params')
    else:
        datasource = create_datasource(
            output_query, data_dir, subjects,  sessions, acquisitions,
            reconstructions)

    if "t1" in datatypes:
        main_workflow.connect(datasource, 'T1',
                              segment_pnh_pipe, 'inputnode.list_T1')

    if "t2" in datatypes:
        main_workflow.connect(datasource, 'T2',
                              segment_pnh_pipe, 'inputnode.list_T2')

    if deriv:

        datasink_name = os.path.join("derivatives", wf_name)

        if "regex_subs" in params.keys():
            params_regex_subs = params["regex_subs"]
        else:
            params_regex_subs = {}

        if "subs" in params.keys():
            params_subs = params["rsubs"]
        else:
            params_subs = {}

        print(datasource.iterables)

        datasink = create_datasink(iterables=datasource.iterables,
                                   name=datasink_name,
                                   params_subs=params_subs,
                                   params_regex_subs=params_regex_subs)

        datasink.inputs.base_directory = process_dir

        if len(datasource.iterables) == 1:
            pref_deriv = "sub-%(sub)s"
            parse_str = r"sub-(?P<sub>\w*)_.*"
        elif len(datasource.iterables) > 1:
            pref_deriv = "sub-%(sub)s_ses-%(ses)s"
            parse_str = r"sub-(?P<sub>\w*)_ses-(?P<ses>\w*)_.*"

        rename_all_brain_derivatives(
            params, main_workflow, segment_pnh_pipe, datasink,
            pref_deriv, parse_str, pad, ssoft, datatypes)

    # running main_workflow
    main_workflow.write_graph(graph2use="colored")
    main_workflow.config['execution'] = {'remove_unnecessary_outputs': 'false'}

    # saving real params.json
    params["macapype_version"] = __version__

    params["full_command"] = cmd

    real_params_file = op.join(process_dir, wf_name, "real_params.json")

    if os.path.exists(real_params_file):
        counter = 0
        while os.path.exists(real_params_file):
            real_params_file = op.join(
                process_dir, wf_name, f"real_params{counter}.json")
            counter += 1

    with open(real_params_file, 'w+') as fp:
        json.dump(params, fp, indent=4)

    if deriv:
        try:
            os.makedirs(op.join(process_dir, datasink_name))
        except OSError:
            print("process_dir {} already exists".format(process_dir))

        real_params_file = op.join(process_dir, datasink_name,
                                   "real_params.json")
        if os.path.exists(real_params_file):
            counter = 0
            while os.path.exists(real_params_file):
                real_params_file = op.join(
                    process_dir, wf_name, f"real_params{counter}.json")
                counter += 1

        with open(real_params_file, 'w+') as fp:
            json.dump(params, fp, indent=4)

    if nprocs is None:
        nprocs = 4

    if "test" not in ssoft:
        if nprocs == 1:
            main_workflow.run()
        else:
            main_workflow.run(plugin='MultiProc',
                              plugin_args={'n_procs': nprocs})


def main():

    # Command line parser
    parser = argparse.ArgumentParser(
        description="PNH segmentation pipeline")

    parser.add_argument("-data", dest="data", type=str, required=True,
                        help="Directory containing MRI data (BIDS)")

    parser.add_argument("-out", dest="out", type=str,  # nargs='+',
                        help="Output dir", required=True)

    parser.add_argument("-soft", dest="soft", type=str,
                        help="Sofware of analysis (SPM or ANTS are defined)",
                        required=True)

    parser.add_argument("-datatypes", "-dt", dest="datatypes", type=str,
                        default=['T1'], nargs='+',
                        help="MRI Datatypes (T1, T2)",
                        required=False)

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

    parser.add_argument("-reorient", dest="reorient", type=str,
                        help="reorient initial image", required=False)

    parser.add_argument("-deriv", dest="deriv", action='store_true',
                        help="output derivatives in BIDS orig directory",
                        required=False)

    parser.add_argument("-pad", "-padback", dest="pad", action='store_true',
                        help="padding mask and seg_mask",
                        required=False)

    args = parser.parse_args()

    cmd = " ".join(sys.argv)

    # main_workflow
    print("Initialising the pipeline...")
    create_main_workflow(
        cmd=cmd,
        data_dir=args.data,
        soft=args.soft,
        process_dir=args.out,
        species=args.species,
        datatypes=args.datatypes,
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
        reorient=args.reorient,
        deriv=args.deriv,
        pad=args.pad)

if __name__ == '__main__':
    main()
