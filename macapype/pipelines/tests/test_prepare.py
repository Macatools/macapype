
import os.path as op

from macapype.utils.utils_tests import make_tmp_dir
from macapype.utils.misc import parse_key
from macapype.pipelines.prepare import (create_short_preparation_pipe,
                                        create_long_single_preparation_pipe,
                                        create_long_multi_preparation_pipe)

data_path = make_tmp_dir()


def test_create_bet_crop_short_preparation_pipe():

    params = {
        "short_preparation_pipe":
        {
            "bet_crop":
            {
            }
        }
    }

    # running workflow
    segment_pnh = create_short_preparation_pipe(
        params=parse_key(params, "short_preparation_pipe"),
        name="short_auto_preparation_pipe")

    segment_pnh.base_dir = data_path

    segment_pnh.write_graph(graph2use="colored")
    assert op.exists(op.join(data_path,
                             "short_auto_preparation_pipe",
                             "graph.png"))


def test_create_bet_crop_reorient_short_preparation_pipe():

    params = {
        "short_preparation_pipe":
        {
            "reorient":
            {
                "new_dims": "x z -y"
            },
            "bet_crop":
            {
            }
        }
    }

    # running workflow
    segment_pnh = create_short_preparation_pipe(
        params=parse_key(params, "short_preparation_pipe"),
        name="short_auto_reorient_preparation_pipe")

    segment_pnh.base_dir = data_path

    segment_pnh.write_graph(graph2use="colored")
    assert op.exists(op.join(data_path,
                             "short_auto_reorient_preparation_pipe",
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
                "norm_intensity":
                {
                    "dimension": 3,
                    "bspline_fitting_distance": 200,
                    "n_iterations": [50, 50, 40, 30],
                    "convergence_threshold": 0.00000001,
                    "shrink_factor": 2,
                    "args": "-r 0 --verbose 1"
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
                "norm_intensity":
                {
                    "dimension": 3,
                    "bspline_fitting_distance": 200,
                    "n_iterations": [50, 50, 40, 30],
                    "convergence_threshold": 0.00000001,
                    "shrink_factor": 2,
                    "args": "-r 0 --verbose 1"
                },
                "denoise":
                {
                    "shrink_factor": 1
                }
            },
            "align_T2_on_T1":
            {
                "dof": 6,
                "cost": "normmi"
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
            "mapnode_prep_T1":
            {
                "crop_T1":
                {
                    "args": ["Should not be used, specific to all",
                             "Should not be used, specific to all"]
                },
                "norm_intensity":
                {
                    "dimension": [3, 3],
                    "bspline_fitting_distance": [200, 200],
                    "n_iterations": [[50, 50, 40, 30], [50, 50, 40, 30]],
                    "convergence_threshold": [0.00000001, 0.00000001],
                    "shrink_factor": [2, 2],
                    "args": ["-r 0 --verbose 1", "-r 0 --verbose 1"]
                },
                "denoise":
                {
                    "shrink_factor": [3, 3]
                }
            },
            "mapnode_prep_T2":
            {
                "crop_T2":
                {
                    "args": ["Should not be used, specific to all"]
                },
                "norm_intensity":
                {
                    "dimension": [3],
                    "bspline_fitting_distance": [200],
                    "n_iterations": [50, 50, 40, 30],
                    "convergence_threshold": [0.00000001],
                    "shrink_factor": [2],
                    "args": ["-r 0 --verbose 1"]
                },
                "denoise":
                {
                    "shrink_factor": [3]
                }
            },
            "align_T2_on_T1":
            {
                "dof": 6,
                "cost": "normmi"
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
