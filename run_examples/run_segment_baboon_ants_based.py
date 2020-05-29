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

package_directory = os.path.dirname(os.path.abspath(__file__))
params_file = '{}/../workflows/params_segment_baboon_ants_based.json'.format(package_directory)
params = json.load(open(params_file))

print(params)
pprint.pprint(params)

# specify own template
params_template = {
    "template_head": "/hpc/meca/users/loh.k/baboon_proc/haiko89_template/Haiko89_Asymmetric.Template_n89.nii.gz",
    "template_brain": "/hpc/meca/users/loh.k/baboon_proc/haiko89_template/Haiko89_Asymmetric.Template_n89.nii.gz",
    "template_gm": "/hpc/meca/users/loh.k/baboon_proc/haiko89_template/TPM_Asymmetric.GreyMatter_Haiko89.nii.gz",
    "template_wm": "/hpc/meca/users/loh.k/baboon_proc/haiko89_template/TPM_Asymmetric.WhiteMatter_Haiko89.nii.gz",
    "template_csf": "/hpc/meca/users/loh.k/baboon_proc/haiko89_template/TPM_Asymmetric.CSF_Haiko89.nii.gz"
}

print (params_template)

data_path = "/hpc/meca/users/loh.k/baboon_proc/data/sub-Babar/ses-test/anat"
main_path = "/hpc/crise/meunier.d/Data"

## data file
T1_file = op.join(data_path, "sub-Babar_ses-test_T1w.nii.gz")
T2_file = op.join(data_path, "sub-Babar_ses-test_T2w.nii.gz")

# running workflow
segment_pnh = create_full_segment_pnh_subpipes(params=params,
                                               params_template=params_template,
                                               name = "test_baboon")
segment_pnh.base_dir = main_path

segment_pnh.inputs.inputnode.T1 = T1_file
segment_pnh.inputs.inputnode.T2 = T2_file

segment_pnh.write_graph(graph2use="colored")
segment_pnh.config['execution'] = {'remove_unnecessary_outputs': 'false'}
segment_pnh.run()
