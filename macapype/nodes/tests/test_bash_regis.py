import os

from macapype.nodes.bash_regis import (T1xT2BET, CropVolume, IterREGBET,
                                       T1xT2BiasFieldCorrection)

data_path = "/hpc/crise/meunier.d/Data/Primavoice/Dataset"

t1_file = os.path.join(data_path,"sub-Apache","ses-01","anat",
                       "sub-Apache_ses-01_T1w.nii")

t2_file = os.path.join(data_path,"sub-Apache","ses-01","anat",
                       "sub-Apache_ses-01_T2w.nii")

mask_file = os.path.join(data_path,"sub-Apache","ses-01","anat",
                       "sub-Apache_ses-01_T1w_mask.nii.gz")

# necesaary for Regis use of FSL with .nii.gz by default
import nipype.interfaces.fsl as fsl
fsl.FSLCommand.set_default_output_type('NIFTI_GZ')


def test_T1xT2BET():

    bet = T1xT2BET()

    bet.inputs.t1_file=t1_file
    bet.inputs.t2_file=t2_file

    val = bet.run().outputs

    assert os.path.exists(val.t1_brain_file)
    assert os.path.exists(val.t2_brain_file)

    os.remove(val.t1_brain_file)
    os.remove(val.t2_brain_file)


def test_T1xT2BET_mask():

    bet = T1xT2BET()

    bet.inputs.t1_file=t1_file
    bet.inputs.t2_file=t2_file
    bet.inputs.m = True

    val = bet.run().outputs

    assert os.path.exists(val.t1_brain_file)
    assert os.path.exists(val.t2_brain_file)

    assert os.path.exists(val.mask_file)

    os.remove(val.t1_brain_file)
    os.remove(val.t2_brain_file)

    os.remove(val.mask_file)

def test_CropVolume():

    crop = CropVolume()

    crop.inputs.i_file=t1_file
    crop.inputs.b_file=mask_file

    val = crop.run().outputs

    assert os.path.exists(val.cropped_file)

    os.remove(val.cropped_file)

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
    val = debias.run().outputs

    assert os.path.exists(val.t1_debiased_file)
    assert os.path.exists(val.t2_debiased_file)

    os.remove(val.t1_debiased_file)
    os.remove(val.t2_debiased_file)


