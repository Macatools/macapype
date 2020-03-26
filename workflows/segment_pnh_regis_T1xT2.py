#!/usr/bin/env python3
"""
    PNH anatomical segmentation pipeline given by Regis Trapeau wrapped in
    Nipype.
    
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
    
    Example
    ---------
    python segment_pnh_regis_T1xT2.py -data /home/bastien/work/data/local_primavoice -out /home/bastien/work/projects/macapype/local_tests -template /home/bastien/work/data/templates/inia19/inia19-t1-brain.nii -priors /home/bastien/work/data/templates/inia19/inia19-prob_0.nii /home/bastien/work/data/templates/inia19/inia19-prob_1.nii /home/bastien/work/data/templates/inia19/inia19-prob_2.nii -ses 01 -sub Maga
    
    Resources files
    -----------------
    Brain templates are required to run this segmentation pipeline. Please,
    download the resources and specify the unzipped directory with the
    '-resources' argument in the command line.
    Resources are here:
    # TODO: find a permanent place
    https://cloud.int.univ-amu.fr/index.php/s/8bCJ5CWWPfHRyHs
    
    Requirements
    --------------
    This workflow use:
        - FSL
    
"""

# Authors : David Meunier (david.meunier@univ-amu.fr)
#           Bastien Cagna (bastien.cagna@univ-amu.fr)
#           Regis Trapeau (regis.trapeau@univ-amu.fr)

import nilearn as ni
import nilearn.image as nii

import nibabel as nb
import os
import os.path as op
import argparse

from bids.layout import BIDSLayout

import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe
import nipype.interfaces.ants as ants
import nipype.interfaces.fsl as fsl

fsl.FSLCommand.set_default_output_type('NIFTI_GZ')


from macapype.pipelines.full_segment import create_full_segment_pnh_T1xT2
from macapype.utils.utils_tests import load_test_data

my_path = "/hpc/crise/meunier.d"

def format_spm_priors(priors, fname="merged_tissue_priors.nii",
                      directory=None):
    """
    Arguments
    =========
    priors: str or list

    fname: str
        Filename of the concatenated 4D Nifti image

    directory: str or None
        If None, the directory of the first file listed in prios is used.
    """
    if isinstance(priors, str):
        img = nb.load(priors)
        if len(img.shape) == 4 and 3 <= img.shape[3] <= 6:
            return priors
        else:
            raise ValueError(
                "Given Nifti is 3D while 4D expected or do not have between 3 "
                "and 6 maps."
            )
    elif isinstance(priors, list):
        imgs = []
        for f in priors:
            if directory is None:
                directory = op.split(f)[0]
            imgs.append(nb.load(f))
        fmt_image = nii.concat_imgs(imgs)

        new_img_f = op.join(directory, fname)
        print(new_img_f)
        nb.save(fmt_image, new_img_f)
        return new_img_f
    raise ValueError(
        "Priors must be one or a list of paths to a Nifti images"
    )


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

    #print("\t", layout.get_acquisitions())



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

"""
def create_infosource(subject_ids):
    infosource = pe.Node(
        interface=niu.IdentityInterface(fields=['subject_id']),
        name="infosource"
    )
    infosource.iterables = [('subject_id', subject_ids)]

    return infosource
"""

# def create_datasource(data_dir, sess):
#     datasource = pe.Node(
#         interface=nio.DataGrabber(infields=['subject_id'], outfields=['T1','T2']),
#         name='datasource'
#     )
#     datasource.inputs.base_directory = data_dir
#     datasource.inputs.template = 'sub-%s/{}/anat/sub-%s_{}_%s.nii'.format(sess, sess)
#     datasource.inputs.template_args = dict(
#         T1=[['subject_id', 'subject_id', "T1w"]],
#         T2=[['subject_id', 'subject_id', "T2w"]],
#     )
#     datasource.inputs.sort_filelist = True
#
#     return datasource

###############################################################################
def create_main_workflow(data_dir, process_dir, subject_ids, sessions,
                         acquisitions, template, priors):
    """ """
    main_workflow = pe.Workflow(name="T1xT2_processing_workflow")
    main_workflow.base_dir = process_dir

    datasource = create_datasource(data_dir, subject_ids, sessions,
                                   acquisitions)

    segment_pnh = create_full_segment_pnh_T1xT2(template, priors)

    main_workflow.connect(
        datasource, 'T1', segment_pnh, 'inputnode.T1')
    main_workflow.connect(
        datasource, 'T2', segment_pnh, 'inputnode.T2')

    return main_workflow


################################################################################
def main(data_path, main_path, subjects, sessions, acquisitions,
         template, priors):
    data_path = op.abspath(data_path)

    if not op.isdir(main_path):
        os.makedirs(main_path)

    # main_workflow
    print("Initialising the pipeline...")
    wf = create_main_workflow(
        data_dir=data_path,
        process_dir=main_path,
        subject_ids=subjects,
        sessions=sessions,
        acquisitions=acquisitions,
        template=template,
        priors=format_spm_priors(priors, directory=main_path)
    )
    # wf.write_graph(graph2use="colored")
    wf.config['execution'] = {'remove_unnecessary_outputs': 'false'}
    print('The PNH segmentation pipeline is ready')
    
    print("Start to process")
    wf.run()
    # wf.run(plugin='MultiProc', plugin_args={'n_procs' : 2})


if __name__ == '__main__':
    # Command line parser
    parser = argparse.ArgumentParser(
        description="PNH segmentation pipeline from Regis Trapeau")
    parser.add_argument("-data", dest="data", type=str, required=True,
                        help="Directory containing MRI data (BIDS)")
    parser.add_argument("-out", dest="out", type=str,
                        help="Output directory", required=True)
    parser.add_argument("-ses", dest="ses", type=str, nargs='+',
                        help="Sessions ID")
    parser.add_argument("-acq", dest="acq", type=str, nargs='+',
                        help="Acquisitions ID")
    parser.add_argument("-subjects", dest="subjects", type=str, nargs='+',
                        help="Subjects' ID", required=False)
    parser.add_argument("-template", dest="template", type=str,
                        default=None, help="Anatomical template")
    parser.add_argument("-priors", dest="priors", type=str, nargs='+',
                        default=None, help="Tissues probability maps")
    args = parser.parse_args()

    if args.template is None and args.priors is None:
        inia_dir = load_test_data("inia19", path_to=my_path)
        args.template = op.join(inia_dir, "inia19-t1-brain.nii")
        args.priors = [
            op.join(inia_dir, "inia19-prob_1.nii"),
            op.join(inia_dir, "inia19-prob_2.nii"),
            op.join(inia_dir, "inia19-prob_0.nii")
        ]
    
    main(
        data_path=args.data,
        main_path=args.out,
        subjects=args.subjects,
        sessions=args.ses,
        acquisitions=args.acq,
        template=args.template,
        priors=args.priors if len(args.priors) > 1 else args.priors[0]
    )

