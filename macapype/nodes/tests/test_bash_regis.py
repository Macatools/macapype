import os

from macapype.nodes.bash_regis import (T1xT2BET, CropVolume, IterREGBET,
                                       T1xT2BiasFieldCorrection)

data_path = "/hpc/crise/meunier.d/Data/Primavoice/Dataset"

t1_file = os.path.join(data_path,"sub-Apache","ses-01","anat",
                       "sub-Apache_ses-01_T1w.nii")

t2_file = os.path.join(data_path,"sub-Apache","ses-01","anat",
                       "sub-Apache_ses-01_T2w.nii")

# necesaary for Regis use of FSL with .nii.gz by default
import nipype.interfaces.fsl as fsl
fsl.FSLCommand.set_default_output_type('NIFTI_GZ')


def test_T1xT2BET():

    bet = T1xT2BET()

    bet.inputs.t1_file=t1_file
    bet.inputs.t2_file=t2_file

    print(bet.cmdline)
    output_file = bet.run().outputs.brain_file
    print(output_file)
    assert os.path.exists(output_file)


#def test_CropVolume():

    #crop = CropVolume()
    #print(crop.cmdline)
    #crop.run()


#def test_IterREGBET():
    #bet = IterREGBET()

    #bet.inputs.t1_file=t1_file
    #bet.inputs.t2_file=t2_file

    #print(bet.cmdline)
    #output_file = bet.run().outputs
    #print(output_file)


def test_T1xT2BiasFieldCorrection():


    debias = T1xT2BiasFieldCorrection()

    debias.inputs.t1_file=t1_file
    debias.inputs.t2_file=t2_file

    print(debias.cmdline)
    output_file = debias.run().outputs.debiased_file
    print(output_file)

    assert os.path.exists(output_file)


