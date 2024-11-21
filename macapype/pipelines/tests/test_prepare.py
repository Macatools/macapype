
import os.path as op

from macapype.utils.utils_tests import make_tmp_dir
from macapype.utils.misc import parse_key
from macapype.pipelines.prepare import create_short_preparation_pipe

data_path = make_tmp_dir()


def test_create_crop_aladin_pipe_short_preparation_pipe():

    params = {
        "short_preparation_pipe":
        {
            "crop_aladin_pipe":
            {
            }
        }
    }

    params_template = {"template_head": ""}

    # running workflow
    segment_pnh = create_short_preparation_pipe(
        params_template=params_template,
        params=parse_key(params, "short_preparation_pipe"),
        name="short_manual_preparation_pipe")

    segment_pnh.base_dir = data_path

    segment_pnh.write_graph(graph2use="colored")
    assert op.exists(op.join(data_path,
                             "short_manual_preparation_pipe",
                             "graph.png"))


def test_create_crop_T1_short_preparation_pipe():

    params = {
        "short_preparation_pipe":
        {
            "crop_T1":
            {
                "args": ""
            }
        }
    }

    params_template = {"template_head": ""}
    # running workflow
    segment_pnh = create_short_preparation_pipe(
        params_template=params_template,
        params=parse_key(params, "short_preparation_pipe"),
        name="short_manual_preparation_pipe")

    segment_pnh.base_dir = data_path

    segment_pnh.write_graph(graph2use="colored")
    assert op.exists(op.join(data_path,
                             "short_manual_preparation_pipe",
                             "graph.png"))
