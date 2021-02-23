import os
import os.path as op

import json
import pprint

import nipype.pipeline.engine as pe

from nipype.interfaces.utility import IdentityInterface
import nipype.interfaces.io as nio

from macapype.pipelines.prepare import (create_short_preparation_pipe,
                                        create_long_single_preparation_pipe,
                                        create_long_multi_preparation_pipe)

# en local
doc_img_path = "../doc/img"

# params params_long_single
params_long_single_file = 'params_long_single.json'
params_long_single = json.load(open(params_long_single_file))

# running workflow
segment_pnh = create_long_single_preparation_pipe(params=params_long_single,
                                               name = "long_single_preparation_pipe")
segment_pnh.base_dir = doc_img_path
segment_pnh.write_graph(graph2use="colored")


# params params_long_multi
params_long_multi_file = 'params_long_multi.json'
params_long_multi = json.load(open(params_long_multi_file))

# running workflow
segment_pnh = create_long_multi_preparation_pipe(params=params_long_multi,
                                               name = "long_multi_preparation_pipe")
segment_pnh.base_dir = doc_img_path
segment_pnh.write_graph(graph2use="colored")

