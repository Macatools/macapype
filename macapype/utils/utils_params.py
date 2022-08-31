import os.path as op

import json
import pprint


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

            print("New params after modification")
            pprint.pprint(params)

            extra_wf_name += "_crop_aladin"
        else:
            print('**** params modification not implemented \
                if no indiv_params ****')

    else:

        indiv_params = json.load(open(indiv_params_file))

        extra_wf_name += "_indiv_params"

        pprint.pprint(indiv_params)

        if "short_preparation_pipe" not in params.keys():

            print("short_preparation_pipe not found in params, \
                not modifying preparation pipe")

        else:

            prep_pipe = "short_preparation_pipe"
            count_all_sessions = 0
            count_T1_crops = 0
            count_long_crops = 0
            count_multi_long_crops = 0

            print("Indiv Params:", indiv_params_file)

            assert op.exists(indiv_params_file), "Error with file {}".format(
                indiv_params_file)

            if subjects is None or sessions is None:
                print("For whole BIDS dir, \
                    unable to assess if the indiv_params is correct")
                print("Running by default short_preparation_pipe and crop_T1")

                if "short_preparation_pipe" in params.keys():

                    if "crop_aladin_T1" in \
                            params["short_preparation_pipe"].keys():

                        print("Deleting crop_aladin_T1")
                        del params["short_preparation_pipe"]["crop_aladin_T1"]

                    if "crop_z_T1" in \
                            params["short_preparation_pipe"].keys():

                        print("Deleting crop_z_T1")
                        del params["short_preparation_pipe"]["crop_z_T1"]

                    print("Adding crop_T1")
                    params["short_preparation_pipe"]["crop_T1"] = \
                        {"args": "should be defined in indiv"}
            else:

                print("Will modify params if necessary, \
                    given specified subjects and sessions;\n")

                for sub in indiv_params.keys():

                    if sub.split('-')[1] not in subjects:
                        print('could not find subject {} in {}'.format(
                            sub.split('-')[1], subjects))
                        continue

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

                            if "crop_T2" in indiv.keys() and 't1' not in ssoft:

                                count_long_crops += 1

                                crop_T1_args = indiv["crop_T1"]["args"]
                                crop_T2_args = indiv["crop_T2"]["args"]
                                if isinstance(crop_T1_args, list) and \
                                        isinstance(crop_T2_args, list):

                                    count_multi_long_crops += 1

                print("count_all_sessions {}".format(count_all_sessions))
                print("count_T1_crops {}".format(count_T1_crops))
                print("count_long_crops {}".format(count_long_crops))
                print("count_multi_long_crops {}".format(
                    count_multi_long_crops))

                if count_all_sessions:
                    if count_multi_long_crops == count_all_sessions:
                        print("**** Found list of crops for T1 and T2\
                            for all sub/ses in indiv -> \
                            long_multi_preparation_pipe")

                        prep_pipe = "long_multi_preparation_pipe"

                        extra_wf_name += "_long_multi"

                    elif count_long_crops == count_all_sessions:

                        print("**** Found crop for T1 and crop for T2\
                            for all sub/ses in indiv -> \
                            long_single_preparation_pipe")

                        prep_pipe = "long_single_preparation_pipe"

                        extra_wf_name += "_long_single"

                    elif count_T1_crops == count_all_sessions:

                        print("**** Found crop for T1 for all \
                            sub/ses in indiv \
                            -> keeping short_preparation_pipe")

                    else:
                        print("**** not all sub/ses have T1 and T2 crops ")
                        print("Error")
                        exit(0)

                if prep_pipe == "short_preparation_pipe":

                    if "crop_aladin_T1" in \
                            params["short_preparation_pipe"].keys():

                        print("Deleting crop_aladin_T1")
                        del params["short_preparation_pipe"]["crop_aladin_T1"]

                    if "crop_z_T1" in \
                            params["short_preparation_pipe"].keys():

                        print("Deleting crop_z_T1")
                        del params["short_preparation_pipe"]["crop_z_T1"]

                    print("Adding crop_T1")
                    params["short_preparation_pipe"]["crop_T1"] = \
                        {"args": "should be defined in indiv"}
                else:

                    params[prep_pipe] = {
                        "prep_T1": {
                            "crop_T1": {
                                "args": "should be defined in indiv"}},
                        "prep_T2": {
                            "crop_T2": {
                                "args": "should be defined in indiv"}},
                        "align_T2_on_T1": {"dof": 6, "cost": "normmi"}}

                    if "denoise" in params["short_preparation_pipe"].keys():
                        denoise = params["short_preparation_pipe"]["denoise"]

                        params[prep_pipe]["prep_T1"]["denoise"] = denoise
                        params[prep_pipe]["prep_T2"]["denoise"] = denoise

                    del params["short_preparation_pipe"]

    # prep for testing only preparation part
    if "prep" in ssoft:
        print("Found prep in soft")

        if "brain_extraction_pipe" in params.keys():
            del params["brain_extraction_pipe"]
            print("Deleting brain_extraction_pipe")

        if "brain_segment_pipe" in params.keys():
            del params["brain_segment_pipe"]
            print("Deleting brain_segment_pipe")

    if "noseg" in ssoft:
        print("Found noseg in soft")
        if "brain_segment_pipe" in params.keys():
            del params["brain_segment_pipe"]
            print("Deleting brain_segment_pipe")

    print("After modif, running with params:")
    pprint.pprint(params)

    return params, indiv_params, extra_wf_name
