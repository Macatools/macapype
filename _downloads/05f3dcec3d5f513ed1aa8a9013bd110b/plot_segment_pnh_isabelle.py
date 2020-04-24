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

import json
import pprint

import nipype.pipeline.engine as pe

from nipype.interfaces.utility import IdentityInterface
import nipype.interfaces.io as nio

###############################################################################
#Running workflow
#==================

from macapype.utils.utils_tests import load_test_data, format_template
from macapype.pipelines.full_pipelines import create_full_segment_pnh_subpipes


from macapype.utils.utils_tests import load_test_data

#package_directory = os.path.dirname(os.path.abspath(__file__))
#params_file = '{}/../workflows/params_segment_pnh_isabelle.json'.format(package_directory)
#params = json.load(open(params_file))

#print(params)
#pprint.pprint(params)

#if "general" in params.keys() and "data_path" in params["general"].keys():
    #data_path = params["general"]["data_path"]
#else:
    #data_path = "/home/INT/meunier.d/ownCloud/Data_tmp/isabelle"
    ##data_path = "/hpc/crise/meunier.d/"
    ##data_path = "/hpc/neopto/USERS/racicot/data/"


#if "general" in params.keys() and "template_name" in params["general"].keys():
    #template_name = params["general"]["template_name"]
#else:
    #template_name = 'NMT_v1.2'

#template_dir = load_test_data(template_name)
#params_template = format_template(template_dir, template_name)
#print (params_template)


##data_path = load_test_data("data_test_macapype", path_to = my_path)

## data file
#T1_file = op.join(data_path, "sub-ziggy_T1w.nii")
#T2_file = op.join(data_path, "sub-ziggy_T2w.nii")

## running workflow
#segment_pnh = create_full_segment_pnh_subpipes(params=params,
                                               #params_template=params_template,
                                               #name = "segment_pnh_subpipes_ziggy")
#segment_pnh.base_dir = data_path

#segment_pnh.inputs.inputnode.T1 = T1_file
#segment_pnh.inputs.inputnode.T2 = T2_file

#segment_pnh.write_graph(graph2use="colored")
##segment_pnh.run()

#exit()

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
