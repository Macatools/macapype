"""
.. _plot_segment_pnh_isabelle:

===================================
Plot the results of a segmentation
===================================
"""

# Authors: David Meunier <david_meunier_79@hotmail.fr>

# License: BSD (3-clause)
# sphinx_gallery_thumbnail_number = 2

import os
import os.path as op

###############################################################################
## Reorient and cropping
##==========================

my_path = "/home/INT/meunier.d/ownCloud/Data_tmp/isabelle/"
wf_path = os.path.join(my_path, "segment_pnh_subpipes_ziggy")


orig_T1_file = op.join(my_path, "sub-ziggy_T1w.nii")

reoriented_T1_file = op.join(wf_path, "preproc_pipe", "reorient_T1_pipe", "swap_dim", "sub-ziggy_T1w_newdims.nii.gz")

cropped_T1_file = op.join(wf_path, "preproc_pipe", "align_crop", "sub-ziggy_T1w_newdims_cropped.nii.gz")

# displaying results
orig_T1 = os.path.join(wf_path, "orig_T1.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {}".format(orig_T1, orig_T1_file)
os.system(cmd)

reoriented_T1 = os.path.join(wf_path, "reoriented_T1.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {}".format(reoriented_T1, reoriented_T1_file)
os.system(cmd)

cropped_T1 = os.path.join(wf_path, "cropped_T1.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {}".format(cropped_T1, cropped_T1_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa

fig, axs = plt.subplots(3, 1, figsize=(32, 16))
axs[0].imshow(plt.imread(orig_T1))
axs[0].axis('off')

axs[1].imshow(plt.imread(reoriented_T1))
axs[1].axis('off')

axs[2].imshow(plt.imread(cropped_T1))
axs[2].axis('off')
plt.show()
