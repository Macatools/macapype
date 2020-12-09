import os.path as op

from macapype.utils.utils_tests import (make_tmp_dir, format_template,
                                        load_test_data)
from macapype.pipelines.full_pipelines import \
    create_full_T1xT2_ants_pnh_subpipes

data_path = make_tmp_dir()


def test_create_full_T1xT2_ants_pnh_subpipes_no_args():

    params = {
        "short_preparation_pipe":
        {
            "bet_crop":
            {
            }
        },
        "brain_extraction_pipe":
        {
            "correct_bias_pipe":
            {
            },
            "extract_pipe":
            {
            }
        },
        "brain_segment_pipe":
        {
            "masked_correct_bias_pipe":
            {
            },
            "register_NMT_pipe":
            {
            },
            "segment_atropos_pipe":
            {
            }
        }
    }

    # params template
    template_name = 'NMT_v1.2'
    template_dir = load_test_data(template_name, data_path)
    params_template = format_template(template_dir, template_name)

    # running workflow
    segment_pnh = create_full_T1xT2_ants_pnh_subpipes(
        params=params, params_template=params_template,
        name="test_create_full_T1xT2_ants_pnh_subpipes_no_args")

    segment_pnh.base_dir = data_path

    segment_pnh.write_graph(graph2use="colored")
    assert op.exists(
        op.join(
            data_path, "test_create_full_T1xT2_ants_pnh_subpipes_no_args",
            "graph.png"))


def test_create_full_T1xT2_ants_pnh_subpipes_no_subpipes():

    params = {
        "short_preparation_pipe":
        {
        },
        "brain_extraction_pipe":
        {
        },
        "brain_segment_pipe":
        {
        }
    }

    # params template
    template_name = 'NMT_v1.2'
    template_dir = load_test_data(template_name, data_path)
    params_template = format_template(template_dir, template_name)

    # running workflow
    segment_pnh = create_full_T1xT2_ants_pnh_subpipes(
        params=params, params_template=params_template,
        name="test_create_full_T1xT2_ants_pnh_subpipes_no_subpipes")

    segment_pnh.base_dir = data_path

    segment_pnh.write_graph(graph2use="colored")
    assert op.exists(
        op.join(data_path,
                "test_create_full_T1xT2_ants_pnh_subpipes_no_subpipes",
                "graph.png"))


def test_create_full_T1xT2_ants_pnh_subpipes():

    params = {
        "short_preparation_pipe":
        {
            "bet_crop":
            {
                "m": True,
                "aT2": True,
                "c": 10,
                "n": 2
            }
        },
        "brain_extraction_pipe":
        {
            "correct_bias_pipe":
            {
                "smooth":
                {
                    "args": "-bin -s 2"
                },
                "norm_smooth":
                {
                    "op_string": "-s 2 -div %s"
                },
                "smooth_bias":
                {
                    "sigma": 2
                }
            },
            "extract_pipe":
            {
                "atlas_brex":
                {
                    "f": 0.5,
                    "reg": 1,
                    "wrp": "10,10,10",
                    "msk": "a,0,0",
                    "dil": 2,
                    "nrm": 1
                }

            }
        },
        "brain_segment_pipe":
        {
            "masked_correct_bias_pipe":
            {
                "smooth":
                {
                    "args": "-bin -s 2"
                },
                "norm_smooth":
                {
                    "op_string": "-s 2 -div %s"
                },
                "smooth_bias":
                {
                        "sigma": 2
                }
            },
            "register_NMT_pipe":
            {
                "norm_intensity":
                {
                    "dimension": 3,
                    "bspline_fitting_distance": 200,
                    "n_iterations": [50, 50, 40, 30],
                    "convergence_threshold": 0.00000001,
                    "shrink_factor": 2,
                    "args": "-r 0 --verbose 1"
                }
            },
            "segment_atropos_pipe":
            {
                "Atropos":
                {
                    "dimension": 3,
                    "numberOfClasses": 3
                },
                "threshold_gm":
                {
                    "thresh": 0.5
                },
                "threshold_wm":
                {
                    "thresh": 0.5
                },
                "threshold_csf":
                {
                    "thresh": 0.5
                }
            }
        }
    }

    # params template
    template_name = 'NMT_v1.2'
    template_dir = load_test_data(template_name, data_path)
    params_template = format_template(template_dir, template_name)

    # running workflow
    segment_pnh = create_full_T1xT2_ants_pnh_subpipes(
        params=params, params_template=params_template,
        name="test_create_full_T1xT2_ants_pnh_subpipes")

    segment_pnh.base_dir = data_path

    segment_pnh.write_graph(graph2use="colored")
    assert op.exists(op.join(data_path,
                             "test_create_full_T1xT2_ants_pnh_subpipes",
                             "graph.png"))
