import os

import nipype.interfaces.spm as spm

from nipype.interfaces.matlab import get_matlab_command
from nipype.interfaces.spm import (no_spm)

def set_spm():

    spm.SPMCommand.set_mlab_paths(matlab_cmd='matlab -nodesktop -nosplash')

    if get_matlab_command() is None:
        print ("could not find matlab, will try with mcr_spm version")

        try:
            spm_dir = os.environ["SPM_DIR"]
            spm_ver = os.environ["SPM_VERSION"]
            mcr_version = os.environ["MCR_VERSION"]
        except KeyError as e:
            print ("Error, could not find SPM or MCR environement")
            return False

        print ("OK, SPM {} MCR version {} was found".format(spm_ver, mcr_version))

        spm_cmd = '{}/run_spm{}.sh /opt/mcr/{} script'.format(
            spm_dir, spm_ver, mcr_version)
        spm.SPMCommand.set_mlab_paths(matlab_cmd=spm_cmd, use_mcr=True)
        return True

    else:
        print ("OK, matlab was found")
        return True
