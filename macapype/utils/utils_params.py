import os.path as op

import json
import pprint


def update_indiv_params(ssoft=[], subjects=None, sessions=None,
                        params=None, indiv_params=None,
                        extra_wf_name=""):

    if "short_preparation_pipe" not in params.keys():

        print("short_preparation_pipe not found in params, \
            not modifying preparation pipe")

    else:

        count_all_sessions = 0
        count_T1_crops = 0

        if subjects is None:
            print("For whole BIDS dir, \
                unable to assess if the indiv_params is correct")
            print("Running by default short_preparation_pipe and crop_T1")

        else:

            print("Will modify params if necessary, \
                given specified subjects and sessions;\n")

            for sub in indiv_params.keys():

                if sub.split('-')[1] not in subjects:
                    print('could not find subject {} in {}'.format(
                        sub.split('-')[1], subjects))
                    continue

                if all([key.split('-')[0] == "ses"
                        for key in indiv_params[sub].keys()]):

                    for ses in indiv_params[sub].keys():

                        if ses.split('-')[1] not in sessions:

                            print('could not find session {} in {}'.format(
                                ses.split('-')[1], sessions))
                            continue

                        count_all_sessions += 1

                        indiv = indiv_params[sub][ses]

                        print(indiv.keys())

                        if "crop_T1" in indiv.keys():
                            count_T1_crops += 1

                else:
                    count_all_sessions += 1

                    indiv = indiv_params[sub]

                    print(indiv.keys())

                    if "crop_T1" in indiv.keys():
                        count_T1_crops += 1

            print("count_all_sessions {}".format(count_all_sessions))
            print("count_T1_crops {}".format(count_T1_crops))

            if count_all_sessions:
                if count_T1_crops == count_all_sessions:

                    print("**** Found crop for T1 for all \
                        sub/ses in indiv \
                        -> keeping short_preparation_pipe")

                    extra_wf_name += "_crop_T1"

                    print("Adding crop_T1")
                    params["short_preparation_pipe"]["crop_T1"] = \
                        {"args": "should be defined in indiv"}

                else:
                    print("**** not all sub/ses have T1 crops,\
                        using autocrop ")

        return params, indiv_params, extra_wf_name


def update_params(ssoft=[], subjects=None, sessions=None,
                  params_file=None, indiv_params_file=None):

    # params
    assert op.exists(params_file), "Error with file {}".format(
        params_file)

    params = json.load(open(params_file))

    extra_wf_name = ""
    indiv_params = {}

    # indiv_params
    if indiv_params_file is None:

        print("No indiv params where found, modifing pipeline to default")

        if "short_preparation_pipe" in params.keys():

            if "crop_T1" in params["short_preparation_pipe"].keys():
                print("Deleting crop_T1")
                del params["short_preparation_pipe"]["crop_T1"]

        else:
            print('**** params modification not implemented \
                if no indiv_params ****')

    else:

        indiv_params = json.load(open(indiv_params_file))

        assert op.exists(indiv_params_file), "Error with file {}".format(
            indiv_params_file)

        pprint.pprint(indiv_params)

        params, indiv_params, extra_wf_name = update_indiv_params(
            ssoft, subjects=subjects, sessions=sessions,
            indiv_params=indiv_params, params=params, extra_wf_name="")

    # modifying crop_aladin
    if "short_preparation_pipe" not in params:
        return params, indiv_params, extra_wf_name

    params_spp = params["short_preparation_pipe"]

    if "crop_aladin_pipe" in params_spp.keys():

        params_spp_cap = params_spp["crop_aladin_pipe"]

        if "robustreg" in ssoft:
            print("Using robustreg option")
            params_spp_cap["reg_T1_on_template"] = {
                    "nac_flag": True,
                    "rig_only_flag": True,
                    "nosym_flag": True,
                    "ln_val": 12,
                    "lp_val": 10,
                    "smoo_r_val": 1.0
                    }

            params_spp_cap["reg_T1_on_template2"] = {
                    "rig_only_flag": True,
                    "nosym_flag": True,
                    "ln_val": 17,
                    "lp_val": 15,
                    "smoo_r_val": 1.0
                    }

        elif "halfrobustreg" in ssoft:
            print("Using halfrobustreg option")
            params_spp_cap["reg_T1_on_template"] = {
                    "nac_flag": True,
                    "rig_only_flag": True,
                    "nosym_flag": True,
                    "ln_val": 12,
                    "lp_val": 10,
                    "smoo_r_val": 1.0
                    }

    print("New params after modification")
    pprint.pprint(params)

    # debias

    if "correct_bias_pipe" in params.keys():
        print("!!!!!! Old version json, correct_bias_pipe is obsolete")
        print("!!!!!! Use fast or N4debias node instead")
        del params["correct_bias_pipe"]

    if "fast" in params.keys():

        print("!! Old version json, moving fast in short_preparation_pipe")
        params["short_preparation_pipe"]["fast"] = params["fast"]
        del params["fast"]

    if "N4debias" in params.keys():

        print("!! Old version json, moving N4debias in short_preparation_pipe")
        params["short_preparation_pipe"]["N4debias"] = params["N4debias"]
        del params["N4debias"]

    # ANTS
    if "ants" in ssoft:
        print("Found ants in soft")

        if "noseg" in ssoft:
            print("Found noseg in soft")
            if "brain_segment_pipe" in params.keys():
                del params["brain_segment_pipe"]
                print("Deleting brain_segment_pipe")

        if "prep" in ssoft:
            print("Found prep in soft")

            # brain mask
            if "extract_pipe" in params.keys():
                del params["extract_pipe"]
                print("Deleting extract_pipe")

            # masked debias
            if "masked_correct_bias_pipe" in params.keys():
                del params["masked_correct_bias_pipe"]
                print("Deleting masked_correct_bias_pipe")

            if "debias" in params.keys():
                del params["debias"]
                print("Deleting debias")

            # segment
            if "brain_segment_pipe" in params.keys():
                del params["brain_segment_pipe"]
                print("Deleting brain_segment_pipe")

    # SPM
    if "spm" in ssoft:
        print("Found spm in soft")

        if "noseg" in ssoft:
            print("Found noseg in soft")
            if "old_segment_pipe" in params.keys():
                del params["old_segment_pipe"]
                print("Deleting old_segment_pipe")

            if "mask_from_seg_pipe" in params.keys():
                del params["mask_from_seg_pipe"]
                print("Deleting mask_from_seg_pipe")

        if "prep" in ssoft:
            print("Found prep in soft")

            if "debias" in params.keys():
                del params["debias"]
                print("Deleting debias")

            if "reg" in params.keys():
                del params["reg"]
                print("Deleting debias")

            if "old_segment_pipe" in params.keys():
                del params["old_segment_pipe"]
                print("Deleting old_segment_pipe")

            if "mask_from_seg_pipe" in params.keys():
                del params["mask_from_seg_pipe"]
                print("Deleting mask_from_seg_pipe")

    print("After modif, running with params:")
    pprint.pprint(params)

    return params, indiv_params, extra_wf_name
