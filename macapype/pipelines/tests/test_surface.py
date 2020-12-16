
import os.path as op

from macapype.utils.utils_tests import make_tmp_dir
from macapype.utils.misc import parse_key
from macapype.pipelines.surface import (create_surface_pipe)

data_path = make_tmp_dir()

def test_create_surface_pipe():

    params = {
        "surface_pipe":
        {
            "bet_crop":
            {
            }
        }
    }

    # running workflow
    segment_pnh = create_surface_pipe(
        params=parse_key(params, "surface_pipe"),
        name="surface_pipe")

    segment_pnh.base_dir = data_path

    segment_pnh.write_graph(graph2use="colored")
    assert op.exists(op.join(data_path,
                             "surface_pipe",
                             "graph.png"))

