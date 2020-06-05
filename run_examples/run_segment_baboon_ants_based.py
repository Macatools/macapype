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

package_directory = os.path.dirname(os.path.abspath(__file__))

# params
params_file = '{}/../workflows/params_segment_baboon_ants_based.json'.format(package_directory)
params = json.load(open(params_file))
print(params)
pprint.pprint(params)

indiv_params_file = '{}/../workflows/indiv_params_segment_baboon_ants_based.json'.format(package_directory)
indiv_params = json.load(open(indiv_params_file))
print(indiv_params)
pprint.pprint(indiv_params)

# template
if "general" in params.keys() and "template_name" in params["general"].keys():
    template_name = params["general"]["template_name"]
else:
    template_name =  'haiko89_template'

template_dir = load_test_data(template_name)
params_template = format_template(template_dir, template_name)
print (params_template)

# en local
data_path = "/home/INT/meunier.d/Data/Baboon/data/sub-Babar/ses-test/anat"
main_path = "/home/INT/meunier.d/data_macapype/"

# sur frioul
#data_path = "/hpc/meca/users/loh.k/baboon_proc/data/sub-Odor/ses-T1/anat"
#main_path = "/hpc/crise/meunier.d/Data"

## data file
T1_file = op.join(data_path, "sub-Odor_ses-T1_T1w.nii.gz")
T2_file = op.join(data_path, "sub-Odor_ses-T1_T2w.nii.gz")

# running workflow
segment_pnh = create_full_segment_pnh_subpipes(params=params,
                                               params_template=params_template,
                                               name = "example_segment_baboon_ants_based_Odor")
segment_pnh.base_dir = main_path

segment_pnh.inputs.inputnode.list_T1 = [T1_file]
segment_pnh.inputs.inputnode.list_T2 = [T2_file]
segment_pnh.inputs.inputnode.indiv_params = indiv_params["sub-Odor"]["ses-T1"]

segment_pnh.write_graph(graph2use="colored")
segment_pnh.config['execution'] = {'remove_unnecessary_outputs': 'false'}
segment_pnh.run()
