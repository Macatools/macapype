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

#orig_data_path = load_test_data("data_test_sphinx_macaque")

###############################################################################
## Data preparation
###############################################################################


################################################################################
### Reorient
###==========================


#orig_T1_file = op.join(orig_data_path, "sub-ziggy_T1w.nii")

## displaying results
#orig_T1 = os.path.join(orig_data_path, "orig_T1.png")
#cmd = "fsleyes render --outfile {} --size 1800 600 {}".format(orig_T1, orig_T1_file)
#os.system(cmd)

#import matplotlib.pyplot as plt  # noqa

#fig, axs = plt.subplots(1, 1, figsize=(36, 24))
#axs.imshow(plt.imread(orig_T1))
#axs.axis('off')

#plt.show()
