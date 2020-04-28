"""
.. _plot_segment_marmo_test:

=================================================================
Plot the results of a segmentation of marmoset data T1w and T2w
=================================================================
"""

# Authors: David Meunier <david_meunier_79@hotmail.fr>

# License: BSD (3-clause)
# sphinx_gallery_thumbnail_number = 2
import os
import os.path as op

import json
import pprint

###############################################################################
# Testing plot in local
#=======================

data_path = "/home/INT/meunier.d/Data/Marmopype/marmo_test/"
wf_path = os.path.join(data_path, "segment_marmo_test_template")

graph = os.path.join(wf_path, "graph.png")

import matplotlib.pyplot as plt  # noqa
img = plt.imread(graph)
plt.figure(figsize=(36, 72))
plt.imshow(img)
plt.axis('off')
plt.show()

###############################################################################
# Preprocessing pipeline
#==========================


###############################################################################
# Cropping
#^^^^^^^^^^^

T1_file = op.join(wf_path, "preproc_pipe", "crop_bb_T1", "T1w_0p33mm_28_roi.nii.gz")

# displaying results
outfile_T1 = os.path.join(wf_path, "outfile_T1.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {}".format(outfile_T1, T1_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(outfile_T1)
plt.figure(figsize=(36, 12))
plt.imshow(img)
plt.axis('off')
plt.show()


###############################################################################
# First part of the pipeline
#=============================

###############################################################################
# Correct bias
#^^^^^^^^^^^^^^^

debiased_T1_file = op.join(wf_path, "correct_bias_pipe", "restore_T1",
                           "T1w_0p33mm_28_roi_maths.nii.gz")


debiased_T1 = os.path.join(wf_path,"debiased_T1.png")

cmd = "fsleyes render --outfile {} --size 1800 600 {}".format(debiased_T1, debiased_T1_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(outfile_T1)

fig, axs = plt.subplots(2, 1, figsize=(36, 24))
axs[0].imshow(plt.imread(outfile_T1))
axs[0].axis('off')

axs[1].imshow(plt.imread(debiased_T1))
axs[1].axis('off')
plt.show()

###############################################################################
# Brain extraction
#^^^^^^^^^^^^^^^^^^

# At the end 1st part pipeline
mask_file = os.path.join(
    wf_path, "devel_atlas_brex", "smooth_mask",
    "T1w_0p33mm_28_roi_maths_noise_corrected_brain_bin_bin.nii.gz")

output_img_overlay = os.path.join(wf_path,"outfile_overlay.png")
#cmd = "fsleyes render --outfile {} --size 800 600 {} -ot mask -o -a 50 {}".format(output_img_overlay, mask_file, T1_file)
cmd = "fsleyes render --outfile {} --size 1800 600 {} {} -a 50".format(output_img_overlay, T1_file, mask_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(output_img_overlay)
plt.figure(figsize=(36, 12))
plt.imshow(img)
plt.axis('off')
plt.show()

###############################################################################
# Second part of the pipeline
#===============================

seg_pipe = op.join(wf_path, "segment_devel_NMT_sub_align")

###############################################################################
# debias T1xT2 and debias N4
#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

denoised_T1_file = os.path.join(seg_pipe, "denoised_pipe", "denoise_T1",
                           "T1w_0p33mm_28_roi_noise_corrected.nii.gz")


denoised_T1 = os.path.join(wf_path,"denoised_T1.png")

cmd = "fsleyes render --outfile {} --size 1800 600 {} -cm Render3".format(denoised_T1, denoised_T1_file)
os.system(cmd)

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
axs[0].imshow(plt.imread(denoised_T1))
axs[0].axis('off')

axs[1].imshow(plt.imread(debiased_mask_T1))
axs[1].axis('off')

axs[2].imshow(plt.imread(N4_debias_T1))
axs[2].axis('off')
plt.show()

###############################################################################
# deoblique
#^^^^^^^^^^^^

## showing mask
T1_file = os.path.join(
   seg_pipe,"register_NMT_pipe", "norm_intensity/",
   "T1w_0p33mm_28_roi_noise_corrected_maths_masked_corrected.nii.gz")

deoblique_T1_file = os.path.join(
    seg_pipe,"segment_atropos_pipe", "deoblique/",
    "T1w_0p33mm_28_roi_noise_corrected_maths_masked_corrected.nii.gz")

outfile_deoblique = os.path.join(wf_path,"outfile_deoblique.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {} -cm red -a 50 {} -cm blue -a 50".format(outfile_deoblique, T1_file, deoblique_T1_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(outfile_deoblique)
plt.figure(figsize=(36, 12))
plt.imshow(img)
plt.axis('off')
plt.show()

###############################################################################
# register template to subject
#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

reg_template_mask_to_T1_file = os.path.join(
    seg_pipe, "register_NMT_pipe", "align_NMT",
    "Template_T1_allineate.nii.gz")

reg_template_mask_to_T1 = os.path.join(wf_path,"reg_template_mask_to_T1.png")


cmd = "fsleyes render --outfile {} --size 1800 600 {} {} -cm red -a 50".format(
    reg_template_mask_to_T1, reg_template_mask_to_T1_file, deoblique_T1_file)

os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(reg_template_mask_to_T1)
plt.figure(figsize=(36, 12))
plt.imshow(img)
plt.axis('off')
plt.show()

###############################################################################
# segmentation
#^^^^^^^^^^^^^^

tissue_file = os.path.join(seg_pipe, "segment_atropos_pipe", "seg_at", "segment_Segmentation.nii.gz")
segmentation = os.path.join(wf_path,"segmentation.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {} {} -dr 0 4 -cm random -a 30".format(segmentation, deoblique_T1_file, tissue_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(segmentation)
plt.figure(figsize=(36, 12))
plt.imshow(img)
plt.axis('off')
plt.show()

###############################################################################
# segmentation results by tissue
#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

csf_file = os.path.join(seg_pipe, "segment_atropos_pipe", "threshold_csf", "segment_SegmentationPosteriors01_thresh.nii.gz")
gm_file = os.path.join(seg_pipe, "segment_atropos_pipe", "threshold_gm", "segment_SegmentationPosteriors02_thresh.nii.gz")
wm_file = os.path.join(seg_pipe, "segment_atropos_pipe", "threshold_wm", "segment_SegmentationPosteriors03_thresh.nii.gz")

segmentation_sep = os.path.join(wf_path,"segmentation_sep.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {} {} -cm red -a 30 {} -cm blue -a 30 {} -cm green -a 30".format(segmentation_sep, deoblique_T1_file, gm_file, wm_file, csf_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(segmentation_sep)
plt.figure(figsize=(36, 12))
plt.imshow(img)
plt.axis('off')
plt.show()


