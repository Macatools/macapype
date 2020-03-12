
import os
import pytest

from macapype.utils.utils_tests import load_test_data
from macapype.nodes.bash_regis import (T1xT2BET, CropVolume, IterREGBET,
                                       T1xT2BiasFieldCorrection)

# Necessary for Regis use of FSL with .nii.gz by default
import nipype.interfaces.fsl as fsl


fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

nmt_dir = load_test_data("NMT_v1.2")
nmt_ss_file = os.path.join(nmt_dir,"NMT_SS.nii.gz")

data_path = "/hpc/crise/meunier.d/Data/Primavoice/data_test"
non_cropped_t1_file = os.path.join(
    data_path, "non_cropped", "sub-Apache_ses-01_T1w.nii")
non_cropped_t2_file = os.path.join(
    data_path, "non_cropped","sub-Apache_ses-01_T2w.nii")
t1_file = os.path.join(data_path, "sub-Apache_ses-01_T1w.nii")
t2_file = os.path.join(data_path, "sub-Apache_ses-01_T2w.nii")
mask_file = os.path.join(data_path, "sub-Apache_ses-01_T1w_mask.nii.gz")
t1_brain_file = os.path.join(data_path, "sub-Apache_ses-01_T1w_SS.nii.gz")


#def run_T1xT2BET_noncropped():

    #bet = T1xT2BET()

    #bet.inputs.t1_file=non_cropped_t1_file
    #bet.inputs.t2_file=non_cropped_t2_file
    #bet.inputs.aT2 = True

    #print(bet.cmdline)

    #val = bet.run().outputs

    #assert os.path.exists(val.t1_brain_file)
    #assert os.path.exists(val.t2_brain_file)
    #assert os.path.exists(val.t2_coreg_file)

    #os.remove(val.t1_brain_file)
    #os.remove(val.t2_brain_file)
    #os.remove(val.t2_coreg_file)


#def run_T1xT2BET_noncropped_mask():

    #bet = T1xT2BET()

    #bet.inputs.t1_file=non_cropped_t1_file
    #bet.inputs.t2_file=non_cropped_t2_file
    #bet.inputs.aT2 = True
    #bet.inputs.m = True

    #print(bet.cmdline)

    #val = bet.run().outputs

    #print(val)

    #assert os.path.exists(val.t1_brain_file)
    #assert os.path.exists(val.t2_brain_file)
    #assert os.path.exists(val.t2_coreg_file)
    #assert os.path.exists(val.mask_file)

    #os.remove(val.t1_brain_file)
    #os.remove(val.t2_brain_file)
    #os.remove(val.t2_coreg_file)
    #os.remove(val.mask_file)


#def run_T1xT2BET_noncropped_mask_cropping():

    #bet = T1xT2BET()

    #bet.inputs.t1_file=non_cropped_t1_file
    #bet.inputs.t2_file=non_cropped_t2_file
    #bet.inputs.aT2 = True
    #bet.inputs.m = True
    #bet.inputs.c = 10

    #print(bet.cmdline)

    #val = bet.run().outputs

    #print(val)

    #assert os.path.exists(val.t1_brain_file)
    #assert os.path.exists(val.t2_brain_file)
    #assert os.path.exists(val.t1_cropped_file)
    #assert os.path.exists(val.t2_cropped_file)
    #assert os.path.exists(val.t2_coreg_file)
    #assert os.path.exists(val.mask_file)

    #os.remove(val.t1_brain_file)
    #os.remove(val.t2_brain_file)
    #os.remove(val.t1_cropped_file)
    #os.remove(val.t2_cropped_file)
    #os.remove(val.t2_coreg_file)
    #os.remove(val.mask_file)


def test_T1xT2BET_noncropped():
    bet = T1xT2BET()

    bet.inputs.t1_file=non_cropped_t1_file
    bet.inputs.t2_file=non_cropped_t2_file

    print(bet.cmdline)

    with pytest.raises(FileNotFoundError):

        val = bet.run().outputs


def test_T1xT2BET():
    bet = T1xT2BET()

    bet.inputs.t1_file=t1_file
    bet.inputs.t2_file=t2_file

    print(bet.cmdline)
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

    print(bet.cmdline)
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


def test_IterREGBET():
    reg_bet = IterREGBET()

    reg_bet.inputs.inw_file=t1_file
    reg_bet.inputs.inb_file=t1_brain_file
    reg_bet.inputs.refb_file=nmt_ss_file

    print(reg_bet)

    val = reg_bet.run().outputs
    print(val)

    assert(val.mask_file)
    assert(val.transfo_file)
    assert(val.inv_transfo_file)

    os.remove(val.mask_file)
    os.remove(val.transfo_file)
    os.remove(val.inv_transfo_file)

#test_IterREGBET()


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


def test_T1xT2BiasFieldCorrection_bet():
    debias = T1xT2BiasFieldCorrection()

    debias.inputs.t1_file=t1_file
    debias.inputs.t2_file=t2_file
    debias.inputs.bet = True

    print(debias.cmdline)
    val = debias.run().outputs

    assert os.path.exists(val.t1_debiased_file)
    assert os.path.exists(val.t2_debiased_file)

    assert os.path.exists(val.t1_debiased_brain_file)
    assert os.path.exists(val.t2_debiased_brain_file)
    assert os.path.exists(val.debiased_mask_file)

    os.remove(val.t1_debiased_file)
    os.remove(val.t2_debiased_file)

    os.remove(val.t1_debiased_brain_file)
    os.remove(val.t2_debiased_brain_file)

    os.remove(val.debiased_mask_file)


def test_T1xT2BiasFieldCorrection_noncropped():
    debias = T1xT2BiasFieldCorrection()

    debias.inputs.t1_file=non_cropped_t1_file
    debias.inputs.t2_file=non_cropped_t2_file

    print(debias.cmdline)
    #val = debias.run().outputs
    with pytest.raises(FileNotFoundError):

        val = debias.run().outputs

#def run_T1xT2BiasFieldCorrection_bet():

    #debias = T1xT2BiasFieldCorrection()

    #debias.inputs.t1_file=non_cropped_t1_file
    #debias.inputs.t2_file=non_cropped_t2_file
    #debias.inputs.aT2 = True
    #debias.inputs.bet = True

    #print(debias.cmdline)
    #val = debias.run().outputs
    #print(val)

    #assert os.path.exists(val.t1_debiased_file)
    #assert os.path.exists(val.t2_debiased_file)
    #assert os.path.exists(val.t1_debiased_brain_file)
    #assert os.path.exists(val.t2_debiased_brain_file)
    #assert os.path.exists(val.t2_coreg_file)
    #assert os.path.exists(val.debiased_mask_file)

    #os.remove(val.t1_debiased_file)
    #os.remove(val.t2_debiased_file)
    #os.remove(val.t1_debiased_brain_file)
    #os.remove(val.t2_debiased_brain_file)
    #os.remove(val.t2_coreg_file)
    #os.remove(val.debiased_mask_file)

#run_T1xT2BiasFieldCorrection_bet()
