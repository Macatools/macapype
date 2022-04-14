import os.path as op

from macapype.utils.utils_tests import (make_tmp_dir, format_template,
                                        load_test_data)
from macapype.pipelines.full_pipelines import \
    create_full_ants_subpipes

def test_create_full_ants_subpipes_no_args():

    params = {
        "general":
        {
            "template_name": "NMT_v1.3better"
        },
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

    data_path = make_tmp_dir()

    # params template
    template_name = params["general"]["template_name"]

    template_dir = load_test_data(template_name, data_path)
    params_template = format_template(template_dir, template_name)

    # running workflow
    segment_pnh = create_full_ants_subpipes(
        params=params, params_template=params_template,
        name="test_create_full_ants_subpipes_no_args")

    segment_pnh.base_dir = data_path

    segment_pnh.write_graph(graph2use="colored")
    assert op.exists(
        op.join(data_path, "test_create_full_ants_subpipes_no_args",
                "graph.png"))


def test_create_full_ants_subpipes_no_subpipes():

    data_path = make_tmp_dir()

    params = {
        "general":
        {
            "template_name": "NMT_v1.3better"
        },
        "short_preparation_pipe":
        {
                "bet_crop":
                {
                }
        },
        "brain_extraction_pipe":
        {
        },
        "brain_segment_pipe":
        {
            "segment_atropos_pipe":
            {
            }
        }
    }

    # params template
    template_name = params["general"]["template_name"]

    template_dir = load_test_data(template_name, data_path)
    params_template = format_template(template_dir, template_name)

    # running workflow
    segment_pnh = create_full_ants_subpipes(
        params=params, params_template=params_template,
        name="test_create_full_ants_subpipes_no_subpipes")

    segment_pnh.base_dir = data_path

    segment_pnh.write_graph(graph2use="colored")
    assert op.exists(
        op.join(data_path,
                "test_create_full_ants_subpipes_no_subpipes",
                "graph.png"))


def test_create_full_ants_subpipes():

    data_path = make_tmp_dir()

    params = {
        "general":
        {
            "template_name": "NMT_v1.3better"
        },
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
                "NMT_subject_align":
                {
                    "afni_ext": "orig"
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
    template_name = params["general"]["template_name"]

    template_dir = load_test_data(template_name, data_path)
    params_template = format_template(template_dir, template_name)

    # running workflow
    segment_pnh = create_full_ants_subpipes(
        params=params, params_template=params_template,
        name="test_create_full_ants_subpipes")

    segment_pnh.base_dir = data_path

    segment_pnh.write_graph(graph2use="colored")
    assert op.exists(op.join(data_path,
                             "test_create_full_ants_subpipes",
                             "graph.png"))

def test_create_full_ants_subpipes_all_default_params():

    from itertools import product
    import json

    species_list = ["marmo", "macaque", "baboon"]
    soft_list = ["ants", "ants_T1"]

    for soft, species in product(soft_list, species_list):

        package_directory = op.dirname(op.abspath(__file__))

        params_file = "{}/../../../workflows/params_segment_{}_{}.json".format(
            package_directory, species, soft)

        assert op.exists(params_file)

        params = json.load(open(params_file))

        data_path = make_tmp_dir()

        # params template
        template_name = params["general"]["template_name"]

        template_dir = load_test_data(template_name, data_path)
        params_template = format_template(template_dir, template_name)

        # running workflow
        segment_pnh = create_full_ants_subpipes(
            params=params, params_template=params_template,
            name="test_create_full_ants_subpipes_all_default_params")

        segment_pnh.base_dir = data_path

        segment_pnh.write_graph(graph2use="colored")
        assert op.exists(op.join(data_path,
                                "test_create_full_ants_subpipes_all_default_params",
                                "graph.png"))

test_create_full_ants_subpipes_all_default_params()