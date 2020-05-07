"""
.. _plot_segment_pnh_spm_based:

===================================================================
Plot the results of a segmentation with SPM-based pipeline T1xT2
===================================================================
"""

# Authors: David Meunier, Bastien Cagna

# License: BSD (3-clause)
# sphinx_gallery_thumbnail_number = 2

import os
import os.path as op

import nipype.pipeline.engine as pe

from nipype.interfaces.utility import IdentityInterface
import nipype.interfaces.io as nio

from macapype.utils.utils_tests import load_test_data

##############################################################################
# Testing plot in local
##############################################################################

data_path = load_test_data("data_test_pnh")

# displaying results
wf_path = os.path.join(data_path, "test_NodeParams_T1xT2")

graph = os.path.join(wf_path, "graph.png")

import matplotlib.pyplot as plt  # noqa
img = plt.imread(graph)
plt.figure(figsize=(36, 72))
plt.imshow(img)
plt.axis('off')
plt.show()


##############################################################################
# Data preparation
##############################################################################

###############################################################################
# Cropping
#===========================

bet_path = os.path.join(wf_path, "data_preparation_pipe", "bet_crop")

T1_file = op.join(bet_path, "sub-Apache_ses-01_T1w_cropped.nii.gz")
print(T1_file)
assert os.path.exists(T1_file)

#outfile_T1 = os.path.join(wf_path, "outfile_T1.png")
#cmd = "fsleyes render --outfile {} --size 1800 600 {}".format(outfile_T1, T1_file)
#os.system(cmd)

#import matplotlib.pyplot as plt  # noqa
#img = plt.imread(outfile_T1)
#plt.figure(figsize=(16, 16))
#plt.imshow(img)
#plt.axis('off')
#plt.show()


###############################################################################
# brain extraction results
#==========================

bet_mask_file = op.join(bet_path, "sub-Apache_ses-01_T1w_BET_mask_cropped.nii.gz")

assert os.path.exists(bet_mask_file)

output_img_overlay = os.path.join(wf_path,"outfile_overlay.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {} {} -cm blue -a 50".format(output_img_overlay, T1_file, bet_mask_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(output_img_overlay)
plt.figure(figsize=(36, 12))
plt.imshow(img)
plt.axis('off')
plt.show()


###############################################################################
# Correct bias results
#==========================

# Comparing Bet results (only if bet is set for T1xT2BiasFieldCorrection)
#debias_path = op.join(wf_path, "debias")
#outfile_debias_mask = os.path.join(wf_path,"outfile_debias_mask.png")
#debias_mask_file = op.join(debias_path, "sub-Apache_ses-01_T1w_cropped_noise_corrected_debiased_BET_mask.nii.gz")
#assert os.path.exists(debias_mask_file)
#cmd = "fsleyes render --outfile {} --size 1800 600 {} {} -cm red -a 33 {} -cm blue -a 33".format(outfile_debias_mask, T1_file, bet_mask_file, debias_mask_file)
#os.system(cmd)


#import matplotlib.pyplot as plt  # noqa
#img = plt.imread(outfile_debias_mask)
#plt.figure(figsize=(36, 12))
#plt.imshow(img)
#plt.axis('off')
#plt.show()




debiased_brain_file = op.join(wf_path, "debias",
                           "sub-Apache_ses-01_T1w_cropped_noise_corrected_debiased_brain.nii.gz")

debiased_T1_brain = os.path.join(wf_path,"debiased_T1_brain.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {} {} -cm red -a 50 ".format(debiased_T1_brain, T1_file, debiased_brain_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(debiased_T1_brain)
plt.figure(figsize=(36, 12))
plt.imshow(img)
plt.axis('off')
plt.show()

###############################################################################
#registration results
#=====================

reg_T1_file = op.join(wf_path,"reg", "sub-Apache_ses-01_T1w_cropped_noise_corrected_debiased_brain_FLIRT-to_inia19-t1-brain.nii")
assert os.path.exists(reg_T1_file)

# showing mask
segment_path = os.path.join(wf_path, "old_segment_pipe")

filled_mask_file = os.path.join(segment_path, "fill_holes", "c1sub-Apache_ses-01_T1w_cropped_noise_corrected_debiased_brain_FLIRT-to_inia19-t1-brain_thresh_maths_maths_ero_filled.nii.gz")
assert os.path.exists(filled_mask_file)

#filled_mask_file = os.path.join(segment_path, "fill_holes_dil", "c1sub-Apache_ses-01_T1w_cropped_debiased_brain_FLIRT-to_inia19-t1-brain_thresh_maths_maths_dil_filled.nii.gz")

outfile_seg_mask = os.path.join(wf_path,"outfile_seg_mask.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {} {} -a 50".format(outfile_seg_mask, reg_T1_file, filled_mask_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(outfile_seg_mask)
plt.figure(figsize=(36, 12))
plt.imshow(img)
plt.axis('off')
plt.show()


###############################################################################
#segmentation results
#=====================

gm_file = os.path.join(segment_path, "threshold_gm", "c1sub-Apache_ses-01_T1w_cropped_noise_corrected_debiased_brain_FLIRT-to_inia19-t1-brain_thresh.nii.gz")
wm_file = os.path.join(segment_path, "threshold_wm", "c2sub-Apache_ses-01_T1w_cropped_noise_corrected_debiased_brain_FLIRT-to_inia19-t1-brain_thresh.nii.gz")
csf_file = os.path.join(segment_path, "threshold_csf", "c3sub-Apache_ses-01_T1w_cropped_noise_corrected_debiased_brain_FLIRT-to_inia19-t1-brain_thresh.nii.gz")

assert os.path.exists(gm_file)
assert os.path.exists(wm_file)
assert os.path.exists(csf_file)

outfile_seg_col = os.path.join(wf_path,"outfile_seg_col.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {} {} {} {}".format(outfile_seg_col, reg_T1_file, gm_file, wm_file, csf_file)
cmd = "fsleyes render --outfile {} --size 1800 600 {} {} -cm red {} -cm blue {} -cm green".format(outfile_seg_col, reg_T1_file, gm_file, wm_file, csf_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(outfile_seg_col)
plt.figure(figsize=(36, 12))
plt.imshow(img)
plt.axis('off')
plt.show()

