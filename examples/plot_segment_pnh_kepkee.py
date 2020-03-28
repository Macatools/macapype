"""
.. _plot_segment:

===================================
Plot the results of a segmentation
===================================
"""

# Authors: David Meunier <david_meunier_79@hotmail.fr>

# License: BSD (3-clause)
# sphinx_gallery_thumbnail_number = 2
import os
import os.path as op

import nipype.pipeline.engine as pe

from nipype.interfaces.utility import IdentityInterface
import nipype.interfaces.io as nio

###############################################################################
# Load test data
from macapype.utils.utils_tests import load_test_data

from macapype.pipelines.full_segment import create_full_segment_pnh_subpipes

my_path = "/hpc/crise/meunier.d/"

data_path = load_test_data("data_test_macapype", path_to = my_path)

## data file
T1_file = op.join(data_path, "sub-Apache_ses-01_T1w.nii")
T2_file = op.join(data_path, "sub-Apache_ses-01_T2w.nii")

from macapype.utils.utils_tests import load_test_data

my_path = "/hpc/crise/meunier.d"

nmt_dir = load_test_data('NMT_v1.2', path_to = my_path)
atlasbrex_dir = load_test_data('AtlasBREX', path_to = my_path)

## running workflow
segment_pnh = create_full_segment_pnh_subpipes(nmt_dir, atlasbrex_dir)
segment_pnh.base_dir = my_path

segment_pnh.inputs.inputnode.T1 = T1_file
segment_pnh.inputs.inputnode.T2 = T2_file

segment_pnh.run()


###############################################################################
# plotting in local

#my_path = "/home/INT/meunier.d/Data/Primavoice/"
## displaying results
#debiased_mask_file = os.path.join(
    #my_path, "T1xT2_segmentation_pipeline", "bet",
    #"sub-Apache_ses-01_T1w_BET_mask_cropped.nii.gz")

#assert os.path.exists(debiased_mask_file)


#output_img = os.path.join(my_path, "T1xT2_segmentation_pipeline","outfile.png")
#cmd = "fsleyes render --outfile {} --size 800 600 {}".format(output_img, debiased_mask_file)
#os.system(cmd)



#output_img_3D = os.path.join(my_path, "T1xT2_segmentation_pipeline","outfile.png")
#cmd = "fsleyes render --scene 3d --outfile {} --size 800 600 {}".format(output_img_3D, debiased_mask_file)
#os.system(cmd)

###############################################################################

# Bet results

data_path = "/home/INT/meunier.d/Data/Primavoice/T1xT2_segmentation_pipeline"
bet_path = os.path.join(data_path, "bet")

"""
# multiple files

T1_file = op.join(bet_path, "sub-Apache_ses-01_T1w_cropped.nii.gz")
mask_file = op.join(bet_path, "sub-Apache_ses-01_T1w_BET_mask_cropped.nii.gz")

output_img_overlay = os.path.join(my_path, "T1xT2_segmentation_pipeline","outfile_overlay.png")
#cmd = "fsleyes render --outfile {} --size 800 600 {} -ot mask -o -a 50 {}".format(output_img_overlay, mask_file, T1_file)
cmd = "fsleyes render --outfile {} --size 800 600 {} {} -a 50".format(output_img_overlay, T1_file, mask_file)
os.system(cmd)




import matplotlib.pyplot as plt  # noqa
img = plt.imread(output_img_overlay)
plt.figure(figsize=(8, 8))
plt.imshow(img)
plt.axis('off')
plt.show()
"""

###############################################################################
# segmentation results
###############################################################################

reg_T1_file = op.join(data_path,"reg", "sub-Apache_ses-01_T1w_cropped_debiased_brain_FLIRT-to_inia19-t1-brain.nii")

# showing mask
segment_path = os.path.join(data_path, "old_segment_extraction_pipe")

#filled_mask_file = os.path.join(segment_path, "fill_holes", "c1sub-Apache_ses-01_T1w_cropped_debiased_brain_FLIRT-to_inia19-t1-brain_thresh_maths_maths_dil_ero_filled.nii.gz")

##filled_mask_file = os.path.join(segment_path, "fill_holes_dil", "c1sub-Apache_ses-01_T1w_cropped_debiased_brain_FLIRT-to_inia19-t1-brain_thresh_maths_maths_dil_filled.nii.gz")

#output_img_overlay = os.path.join(data_path,"outfile_overlay.png")
##cmd = "fsleyes render --outfile {} --size 800 600 {} -ot mask -o -a 50 {}".format(output_img_overlay, mask_file, T1_file)
#cmd = "fsleyes render --outfile {} --size 800 600 {} {} -a 50".format(output_img_overlay, reg_T1_file, filled_mask_file)
#os.system(cmd)

#import matplotlib.pyplot as plt  # noqa
#img = plt.imread(output_img_overlay)
#plt.figure(figsize=(8, 8))
#plt.imshow(img)
#plt.axis('off')
#plt.show()

# showing tissues




gm_file = os.path.join(segment_path, "threshold_gm", "c1sub-Apache_ses-01_T1w_cropped_debiased_brain_FLIRT-to_inia19-t1-brain_thresh.nii.gz")
wm_file = os.path.join(segment_path, "threshold_wm", "c2sub-Apache_ses-01_T1w_cropped_debiased_brain_FLIRT-to_inia19-t1-brain_thresh.nii.gz")
csf_file = os.path.join(segment_path, "threshold_csf", "c3sub-Apache_ses-01_T1w_cropped_debiased_brain_FLIRT-to_inia19-t1-brain_thresh.nii.gz")

#filled_mask_file = os.path.join(segment_path, "fill_holes_dil", "c1sub-Apache_ses-01_T1w_cropped_debiased_brain_FLIRT-to_inia19-t1-brain_thresh_maths_maths_dil_filled.nii.gz")

output_img_overlay = os.path.join(data_path,"outfile_overlay.png")
cmd = "fsleyes render --outfile {} --size 800 600 {} {} {} {}".format(output_img_overlay, reg_T1_file, gm_file, wm_file, csf_file)
cmd = "fsleyes render --outfile {} --size 800 600 {} {} -cm red {} -cm blue {} -cm green".format(output_img_overlay, reg_T1_file, gm_file, wm_file, csf_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(output_img_overlay)
plt.figure(figsize=(8, 8))
plt.imshow(img)
plt.axis('off')
plt.show()
