
from bids.layout import BIDSLayout

import nipype.interfaces.io as nio
import nipype.pipeline.engine as pe


def create_datasource(data_dir, subjects=None, sessions=None, acqs=None):
    """ Create a datasource node that have iterables following BIDS format """
    bids_datasource = pe.Node(
        interface=nio.BIDSDataGrabber(),
        name='bids_datasource'
    )

    bids_datasource.inputs.base_dir = data_dir
    bids_datasource.inputs.output_query = {
        'T1': {
            "datatype": "anat", "suffix": "T1w",
            "extensions": ["nii", ".nii.gz"]
        },
        'T2': {
            "datatype": "anat", "suffix": "T2w",
            "extensions": ["nii", ".nii.gz"]
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

    if acqs is not None:
        iterables.append(('acquisition', acqs))

    bids_datasource.iterables = iterables

    return bids_datasource
