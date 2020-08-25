"""
.. _plot_segment_marmo_ants_based:

===============================================================================
Plot the results of a segmentation of marmoset data with ANTS-based pipeline
===============================================================================
"""

# Authors: David Meunier <david_meunier_79@hotmail.fr>

# License: BSD (3-clause)
# sphinx_gallery_thumbnail_number = 2
import os
import os.path as op

import json
import pprint

from macapype.utils.utils_tests import load_test_data

##############################################################################
# Testing plot in local
##############################################################################

data_path = load_test_data("data_test_marmo")

wf_path = os.path.join(data_path, "example_segment_marmo_ants_based")

graph = os.path.join(wf_path, "graph.png")

import matplotlib.pyplot as plt  # noqa
img = plt.imread(graph)
plt.figure(figsize=(36, 72))
plt.imshow(img)
plt.axis('off')
plt.show()


###############################################################################
# Data preparation
###############################################################################

prep_path = op.join(wf_path, "old_data_preparation_pipe")

###############################################################################
# results of cropping
#===========================

cropped_T1_file = op.join(prep_path, "crop_T1", "T1w_0p33mm_28_roi.nii.gz")

assert op.exists(cropped_T1_file), "Error with {}".format(cropped_T1_file)

# displaying results
cropped_T1 = os.path.join(wf_path, "cropped_T1.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {}".format(cropped_T1,
                                                              cropped_T1_file)
os.system(cmd)


cropped_T2_file = op.join(prep_path, "crop_T2",
                          "T2w_0p4mm_32_flirt_roi.nii.gz")

assert op.exists(cropped_T2_file), "Error with {}".format(cropped_T2_file)

# displaying results
cropped_T2 = os.path.join(wf_path, "cropped_T2.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {}".format(cropped_T2,
                                                              cropped_T2_file)
os.system(cmd)


###############################################################################
# results of denoising
#===========================

denoise_T1_file = op.join(
    prep_path, "denoise_T1",
    "T1w_0p33mm_28_roi_noise_corrected.nii.gz")

assert op.exists(denoise_T1_file), "Error with {}".format(denoise_T1_file)


# displaying results
denoise_T1 = os.path.join(wf_path, "denoise_T1.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {}".format(denoise_T1, denoise_T1_file)
os.system(cmd)


denoise_T2_file = op.join(
    prep_path, "denoise_T2",
    "T2w_0p4mm_32_flirt_roi_noise_corrected.nii.gz")

assert op.exists(denoise_T2_file), "Error with {}".format(denoise_T2_file)

# displaying results
denoise_T2 = os.path.join(wf_path, "denoise_T2.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {}".format(denoise_T2,
                                                              denoise_T2_file)
os.system(cmd)

################################################################################

fig, axs = plt.subplots(2, 1, figsize=(36, 24))
axs[0].imshow(plt.imread(cropped_T1))
axs[0].axis('off')

axs[1].imshow(plt.imread(denoise_T1))
axs[1].axis('off')

plt.show()

fig, axs = plt.subplots(2, 1, figsize=(36, 24))
axs[0].imshow(plt.imread(cropped_T2))
axs[0].axis('off')

axs[1].imshow(plt.imread(denoise_T2))
axs[1].axis('off')

plt.show()

##############################################################################
# First part of the pipeline: brain extraction
##############################################################################

###############################################################################
# Correct bias results
#==========================

debiased_T1_file = op.join(wf_path, "brain_extraction_pipe", "correct_bias_pipe", "restore_T1",
                           "T1w_0p33mm_28_roi_noise_corrected_maths.nii.gz")

debiased_T1 = os.path.join(wf_path,"debiased_T1.png")

cmd = "fsleyes render --outfile {} --size 1800 600 {}".format(debiased_T1, debiased_T1_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
fig, axs = plt.subplots(2, 1, figsize=(36, 24))
axs[0].imshow(plt.imread(cropped_T1))
axs[0].axis('off')

axs[1].imshow(plt.imread(debiased_T1))
axs[1].axis('off')
plt.show()

###############################################################################
# Brain extraction results
#==========================

# At the end 1st part pipeline
smooth_mask_file = os.path.join(
    wf_path, "brain_extraction_pipe", "extract_pipe", "smooth_mask",
    "T1w_0p33mm_28_roi_noise_corrected_maths_brain_bin_bin.nii.gz")

smooth_mask = os.path.join(wf_path,"smooth_mask.png")
#cmd = "fsleyes render --outfile {} --size 800 600 {} -ot mask -o -a 50 {}".format(output_img_overlay, mask_file, T1_file)
cmd = "fsleyes render --outfile {} --size 1800 600 {} {} -a 50".format(smooth_mask, cropped_T1_file, smooth_mask_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(smooth_mask)
plt.figure(figsize=(36 , 12))
plt.imshow(img)
plt.axis('off')
plt.show()

##############################################################################
# Second part of the pipeline: segmentation
##############################################################################

seg_pipe = op.join(wf_path, "brain_segment_from_mask_pipe")

###############################################################################
# debias T1xT2 and debias N4
#=============================

debiased_mask_T1_file = os.path.join(seg_pipe, "masked_correct_bias_pipe", "restore_mask_T1",
                         "T1w_0p33mm_28_roi_noise_corrected_maths_masked.nii.gz")

debiased_mask_T1 = os.path.join(wf_path,"debiased_mask_T1.png")

cmd = "fsleyes render --outfile {} --size 1800 600 {} -cm Render3".format(debiased_mask_T1, debiased_mask_T1_file)
os.system(cmd)


N4_debias_T1_file = os.path.join(seg_pipe, "register_NMT_pipe", "norm_intensity",
                         "T1w_0p33mm_28_roi_noise_corrected_maths_masked_corrected.nii.gz")

N4_debias_T1 = os.path.join(wf_path,"N4_debias_T1.png")

cmd = "fsleyes render --outfile {} --size 1800 600 {} -cm Render3".format(N4_debias_T1, N4_debias_T1_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa

fig, axs = plt.subplots(3, 1, figsize=(36, 36))
axs[0].imshow(plt.imread(denoise_T1))
axs[0].axis('off')

axs[1].imshow(plt.imread(debiased_mask_T1))
axs[1].axis('off')

axs[2].imshow(plt.imread(N4_debias_T1))
axs[2].axis('off')
plt.show()


###############################################################################
# register template to subject
#==============================

deoblique_T1_file = os.path.join(
     seg_pipe, "register_NMT_pipe",  "deoblique",
    "T1w_0p33mm_28_roi_noise_corrected_maths_masked_corrected.nii.gz")

reg_template_mask_to_T1_file = os.path.join(
    seg_pipe, "register_NMT_pipe", "align_NMT",
    "Template_T1_allineate.nii.gz")

reg_template_mask_to_T1 = os.path.join(wf_path,"reg_template_mask_to_T1.png")


cmd = "fsleyes render --outfile {} --size 1800 600 {} {} -a 50 -cm blue".format(
    reg_template_mask_to_T1, reg_template_mask_to_T1_file, deoblique_T1_file)

os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(reg_template_mask_to_T1)
plt.figure(figsize=(36 , 12))
plt.imshow(img)
plt.axis('off')
plt.show()

###############################################################################
# segmentation results by tissue
#================================

csf_file = os.path.join(seg_pipe, "segment_atropos_pipe", "threshold_csf", "segment_SegmentationPosteriors01_thresh.nii.gz")
gm_file = os.path.join(seg_pipe, "segment_atropos_pipe", "threshold_gm", "segment_SegmentationPosteriors02_thresh.nii.gz")
wm_file = os.path.join(seg_pipe, "segment_atropos_pipe", "threshold_wm", "segment_SegmentationPosteriors03_thresh.nii.gz")

segmentation_sep = os.path.join(wf_path,"segmentation_sep.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {} {} -cm red -a 30 {} -cm blue -a 30 {} -cm green -a 30".format(segmentation_sep, debiased_mask_T1_file, gm_file, wm_file, csf_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(segmentation_sep)
plt.figure(figsize=(36 , 12))
plt.imshow(img)
plt.axis('off')
plt.show()

