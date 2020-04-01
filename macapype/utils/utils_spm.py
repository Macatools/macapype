import os
import os.path as op

import nilearn.image as nii

import nibabel as nb

import nipype.interfaces.spm as spm
from nipype.interfaces.matlab import get_matlab_command


def set_spm():

    spm.SPMCommand.set_mlab_paths(matlab_cmd='matlab -nodesktop -nosplash')

    if get_matlab_command() is None:
        print("could not find matlab, will try with mcr_spm version")

        try:
            spm_dir = os.environ["SPM_DIR"]
            spm_ver = os.environ["SPM_VERSION"]
            mcr_version = os.environ["MCR_VERSION"]
        except KeyError:
            print("Error, could not find SPM or MCR environement")
            return False

        print("OK, SPM {} MCR version {} was found".format(spm_ver,
                                                           mcr_version))

        spm_cmd = '{}/run_spm{}.sh /opt/mcr/{} script'.format(
            spm_dir, spm_ver, mcr_version)
        spm.SPMCommand.set_mlab_paths(matlab_cmd=spm_cmd, use_mcr=True)
        return True

    else:
        print("OK, matlab was found")
        return True


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
    print("Formatting spm priors")

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
        print("Finished Formatting spm priors")
        return new_img_f
    raise ValueError(
        "Priors must be one or a list of paths to a Nifti images"
    )
