
import os.path as op

from macapype.utils.utils_tests import make_tmp_dir
from macapype.utils.misc import parse_key
from macapype.pipelines.prepare import (create_short_preparation_pipe,
                                        create_long_single_preparation_pipe,
                                        create_long_multi_preparation_pipe)

data_path = make_tmp_dir()


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

    # running workflow
    segment_pnh = create_short_preparation_pipe(
        params=parse_key(params, "short_preparation_pipe"),
        name="short_manual_preparation_pipe")

    segment_pnh.base_dir = data_path

    segment_pnh.write_graph(graph2use="colored")
    assert op.exists(op.join(data_path,
                             "short_manual_preparation_pipe",
                             "graph.png"))


def test_create_long_single_preparation_pipe():

    params = {
        "long_single_preparation_pipe":
        {
            "prep_T1":
            {
                "crop_T1":
                {
                    "args": "should be defined in indiv"
                },
                "denoise":
                {
                    "shrink_factor": 1
                }
            },
            "prep_T2":
            {
                "crop_T2":
                {
                    "args": "should be defined in indiv"
                },
                "denoise":
                {
                    "shrink_factor": 1
                }
            },
            "align_T2_on_T1":
            {
            }
        }
    }

    # running workflow
    segment_pnh = create_long_single_preparation_pipe(
        params=parse_key(params, "long_single_preparation_pipe"),
        name="long_single_preparation_pipe")

    segment_pnh.base_dir = data_path

    segment_pnh.write_graph(graph2use="colored")
    assert op.exists(op.join(data_path,
                             "long_single_preparation_pipe",
                             "graph.png"))


def test_create_long_multi_preparation_pipe():

    params = {
        "long_multi_preparation_pipe":
        {
            "prep_T1":
            {
                "crop_T1":
                {
                    "args": ["Should not be used, specific to all",
                             "Should not be used, specific to all"]
                },
                "denoise":
                {
                    "shrink_factor": [3, 3]
                }
            },
            "prep_T2":
            {
                "crop_T2":
                {
                    "args": ["Should not be used, specific to all"]
                },
                "denoise":
                {
                    "shrink_factor": [3]
                }
            },
            "align_T2_on_T1":
            {
            }
        }
    }

    # running workflow
    segment_pnh = create_long_multi_preparation_pipe(
        params=parse_key(params, "long_multi_preparation_pipe"),
        name="long_multi_preparation_pipe")

    segment_pnh.base_dir = data_path

    segment_pnh.write_graph(graph2use="colored")
    assert op.exists(op.join(data_path,
                             "long_multi_preparation_pipe",
                             "graph.png"))
