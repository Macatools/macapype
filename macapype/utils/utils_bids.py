
from bids.layout import BIDSLayout

import nipype.interfaces.io as nio
import nipype.pipeline.engine as pe

from .utils_nodes import BIDSDataGrabberParams


def create_datasource(data_dir, subjects=None, sessions=None,
                      acquisitions=None, records=None):
    """ Create a datasource node that have iterables following BIDS format """
    bids_datasource = pe.Node(
        interface=nio.BIDSDataGrabber(),
        name='bids_datasource'
    )

    bids_datasource.inputs.base_dir = data_dir
    bids_datasource.inputs.output_query = {
        'T1': {
            "datatype": "anat", "suffix": "T1w",
            "extension": ["nii", ".nii.gz"]
        },
        'T2': {
            "datatype": "anat", "suffix": "T2w",
            "extension": ["nii", ".nii.gz"]
        }
    }

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

    if sessions!=[]: 
        iterables.append(('session', sessions))

    if acquisitions is not None:
        iterables.append(('acquisition', acquisitions))

    if records is not None:
        iterables.append(('record', records))

    bids_datasource.iterables = iterables

    return bids_datasource


def create_datasource_indiv_params(data_dir, indiv_params, subjects=None,
                                   sessions=None, acquisitions=None,
                                   records=None):
    """ Create a datasource node that have iterables following BIDS format,
    including a indiv_params file"""

    bids_datasource = pe.Node(
        interface=BIDSDataGrabberParams(indiv_params),
        name='bids_datasource'
    )

    bids_datasource.inputs.base_dir = data_dir
    bids_datasource.inputs.output_query = {
        'T1': {
            "datatype": "anat", "suffix": "T1w",
            "extension": ["nii", ".nii.gz"]
        },
        'T2': {
            "datatype": "anat", "suffix": "T2w",
            "extension": ["nii", ".nii.gz"]
        }
    }

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

    if records is not None:
        iterables.append(('record', records))

    bids_datasource.iterables = iterables

    return bids_datasource


# noT1
def create_datasource_noT1(data_dir, subjects=None, sessions=None,
                           acquisitions=None, records=None):
    """ Create a datasource node that have iterables following BIDS format """
    bids_datasource = pe.Node(
        interface=nio.BIDSDataGrabber(),
        name='bids_datasource'
    )

    bids_datasource.inputs.base_dir = data_dir
    bids_datasource.inputs.output_query = {
        'T1': {
            "datatype": "anat", "suffix": "T1w",
            "extension": ["nii", ".nii.gz"]
        }
    }

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

    if records is not None:
        iterables.append(('record', records))

    bids_datasource.iterables = iterables

    return bids_datasource


def create_datasource_indiv_params_noT1(data_dir, indiv_params, subjects=None,
                                        sessions=None, acquisitions=None):
    """ Create a datasource node that have iterables following BIDS format,
    including a indiv_params file"""

    bids_datasource = pe.Node(
        interface=BIDSDataGrabberParams(indiv_params),
        name='bids_datasource'
    )

    bids_datasource.inputs.base_dir = data_dir
    bids_datasource.inputs.output_query = {
        'T1': {
            "datatype": "anat", "suffix": "T1w",
            "extension": ["nii", ".nii.gz"]
        }
    }

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

    bids_datasource.iterables = iterables

    return bids_datasource
