"""
.. _plot_segment_sphinx_macaque_ants_based:

==============================================================================
Plot the results of a segmentation with ANTS-based pipeline in sphinx position
==============================================================================
"""

# Authors: David Meunier, Bastien Cagna

# License: BSD (3-clause)
# sphinx_gallery_thumbnail_number = 2

import os
import os.path as op

from macapype.utils.utils_tests import load_test_data

##############################################################################
# Testing plot in local
##############################################################################

data_path = load_test_data("data_test_sphinx_macaque")

wf_path = os.path.join(data_path, "example_segment_sphinx_macaque_ants_based")

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
## Reorient
##==========================


orig_T1_file = op.join(data_path, "sub-ziggy_T1w.nii")

reoriented_T1_file = op.join(wf_path, "old_data_preparation_pipe", "reorient_T1_pipe", "swap_dim", "sub-ziggy_T1w_newdims.nii.gz")

# displaying results
orig_T1 = os.path.join(wf_path, "orig_T1.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {}".format(orig_T1, orig_T1_file)
os.system(cmd)

reoriented_T1 = os.path.join(wf_path, "reoriented_T1.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {}".format(reoriented_T1, reoriented_T1_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa

fig, axs = plt.subplots(2, 1, figsize=(36, 24))
axs[0].imshow(plt.imread(orig_T1))
axs[0].axis('off')

axs[1].imshow(plt.imread(reoriented_T1))
axs[1].axis('off')

plt.show()

###############################################################################
## Cropping and denoise
##==========================

cropped_T1_file = op.join(wf_path, "old_data_preparation_pipe", "bet_crop", "sub-ziggy_T1w_newdims_cropped.nii.gz")
assert os.path.exists(cropped_T1_file), "Error with {}".format(cropped_T1_file)

cropped_T1 = os.path.join(wf_path, "cropped_T1.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {}".format(cropped_T1, cropped_T1_file)
os.system(cmd)


denoised_T1_file = op.join(wf_path, "old_data_preparation_pipe", "denoise_T1", "sub-ziggy_T1w_newdims_cropped_noise_corrected.nii.gz")

denoised_T1 = os.path.join(wf_path, "denoised_T1.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {}".format(denoised_T1, denoised_T1_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa

fig, axs = plt.subplots(2, 1, figsize=(36, 24))
axs[0].imshow(plt.imread(cropped_T1))
axs[0].axis('off')

axs[1].imshow(plt.imread(denoised_T1))
axs[1].axis('off')

plt.show()


