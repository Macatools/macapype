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
params_file = '{}/../workflows/params_segment_marmo_ants_based.json'.format(package_directory)
params = json.load(open(params_file))

print(params)
pprint.pprint(params)

# template
if "general" in params.keys() and "template_name" in params["general"].keys():
    template_name = params["general"]["template_name"]
else:
    template_name =  'marmotemplate'

template_dir = load_test_data(template_name)
params_template = format_template(template_dir, template_name)
print (params_template)

# data
if "general" in params.keys() and "my_path" in params["general"].keys():
    my_path = params["general"]["my_path"]
else:
    my_path = ''

data_path = load_test_data("data_test_marmo", my_path)

# data file
T1_file = op.join(data_path, "T1w_0p33mm_28.nii")
T2_file = op.join(data_path, "T2w_0p4mm_32.nii")

from macapype.utils.utils_tests import load_test_data

# running workflow
segment_pnh = create_full_segment_pnh_subpipes(params=params,
                                               params_template=params_template,
                                               name = "example_segment_marmo_ants_based")
segment_pnh.base_dir = data_path

segment_pnh.inputs.inputnode.list_T1 = [T1_file]
segment_pnh.inputs.inputnode.list_T2 = [T2_file]

segment_pnh.write_graph(graph2use="colored")
segment_pnh.run()
