import os.path as op

import json

from bids.layout import BIDSLayout

import nipype.interfaces.io as nio
import nipype.pipeline.engine as pe

from .utils_nodes import BIDSDataGrabberParams


def create_datasource(output_query, data_dir, subjects=None, sessions=None,
                      acquisitions=None, reconstructions=None):
    """ Create a datasource node that have iterables following BIDS format """
    bids_datasource = pe.Node(
        interface=nio.BIDSDataGrabber(),
        name='bids_datasource'
    )

    bids_datasource.inputs.base_dir = data_dir
    bids_datasource.inputs.output_query = output_query

    layout = BIDSLayout(data_dir)

    # Verbose
    print("BIDS layout:", layout)
    print("\t", layout.get_subjects())
    print("\t", layout.get_sessions())

    if subjects is None:
        subjects = layout.get_subjects()

    if sessions is None:
        sessions = layout.get_sessions()

    iterables = []
    iterables.append(('subject', subjects))

    if sessions != []:
        iterables.append(('session', sessions))

    if acquisitions is not None:
        iterables.append(('acquisition', acquisitions))

    if reconstructions is not None:
        iterables.append(('reconstruction', reconstructions))

    bids_datasource.iterables = iterables

    return bids_datasource


def create_datasource_indiv_params(output_query, data_dir, indiv_params,
                                   subjects=None, sessions=None,
                                   acquisitions=None, reconstructions=None):
    """ Create a datasource node that have iterables following BIDS format,
    including a indiv_params file"""

    bids_datasource = pe.Node(
        interface=BIDSDataGrabberParams(indiv_params),
        name='bids_datasource'
    )

    bids_datasource.inputs.base_dir = data_dir
    bids_datasource.inputs.output_query = output_query

    layout = BIDSLayout(data_dir)

    # Verbose
    print("BIDS layout:", layout)
    print("\t", layout.get_subjects())
    print("\t", layout.get_sessions())

    if subjects is None:
        subjects = layout.get_subjects()

    if sessions is None:
        sessions = layout.get_sessions()

    iterables = []
    iterables.append(('subject', subjects))
    iterables.append(('session', sessions))

    if acquisitions is not None:
        iterables.append(('acquisition', acquisitions))

    if reconstructions is not None:
        iterables.append(('reconstruction', reconstructions))

    bids_datasource.iterables = iterables

    return bids_datasource


def create_datasink(iterables, name="output", params_subs={},
                    params_regex_subs={}):
    """
    Description: reformating relevant outputs
    """

    print("Datasink name: ", name)

    datasink = pe.Node(nio.DataSink(container=name),
                       name='datasink')

    subjFolders = [
        ('_session_%s_subject_%s' % (ses, sub),
         'sub-%s/ses-%s/anat' % (sub, ses)) for ses in iterables[1][1]
        for sub in iterables[0][1]]

    # subs
    json_subs = op.join(op.dirname(op.abspath(__file__)),
                        "subs.json")

    dict_subs = json.load(open(json_subs))

    dict_subs.update(params_subs)

    print(dict_subs)

    subs = [(key, value) for key, value in dict_subs.items()]

    subjFolders.extend(subs)

    print(subjFolders)

    datasink.inputs.substitutions = subjFolders

    # regex_subs
    json_regex_subs = op.join(op.dirname(op.abspath(__file__)),
                              "regex_subs.json")

    dict_regex_subs = json.load(open(json_regex_subs))

    dict_regex_subs.update(params_regex_subs)

    regex_subs = [(key, value) for key, value in dict_regex_subs.items()]

    datasink.inputs.regexp_substitutions = regex_subs

    return datasink
