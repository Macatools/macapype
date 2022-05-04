import os.path as op

from itertools import product

from pathlib import Path

from macapype.utils.utils_tests import (make_tmp_dir, format_template,
                                        load_test_data)
from macapype.pipelines.full_pipelines import \
    (create_full_ants_subpipes, create_full_T1_ants_subpipes,
     create_full_spm_subpipes)

cwd = Path.cwd()
data_path = make_tmp_dir()


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
                "NMT_subject_align":
                {
                }
            },
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
        name="test_create_full_ants_subpipes_no_args")

    segment_pnh.base_dir = data_path

    segment_pnh.write_graph(graph2use="colored")
    assert op.exists(
        op.join(data_path, "test_create_full_ants_subpipes_no_args",
                "graph.png"))


def test_create_full_ants_subpipes_no_subpipes():

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
            "register_NMT_pipe":
            {
                "NMT_subject_align":
                {
                }
            },
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

    import os
    import json

    softs = ["ants"]
    all_species = ["marmo", "macaque", 'baboon']
    spaces = ["native", "template"]

    for soft, species, space in product(softs, all_species, spaces):

        print("*** Testing soft {} with species {}".format(soft, species))

        wf_dir = (cwd / "workflows").resolve()
        print(wf_dir)

        params_file = os.path.join(wf_dir,  "params_segment_{}_{}.json".format(
            species, soft))

        assert op.exists(params_file), \
            "Could not find params_file {}".format(params_file)

        params = json.load(open(params_file))

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
        assert op.exists(
            op.join(data_path,
                    "test_create_full_ants_subpipes_all_default_params",
                    "graph.png"))


def test_create_full_ants_t1_subpipes_all_default_params():

    import os
    import json

    softs = ["ants"]
    all_species = ["marmo", "macaque", 'baboon']
    spaces = ["native", "template"]

    for soft, species, space in product(softs, all_species, spaces):

        print("*** Testing soft {} with species {}".format(soft, species))

        wf_dir = (cwd / "workflows").resolve()
        print(wf_dir)

        params_file = os.path.join(wf_dir,  "params_segment_{}_{}.json".format(
            species, soft))

        assert op.exists(params_file), \
            "Could not find params_file {}".format(params_file)

        params = json.load(open(params_file))

        # params template
        template_name = params["general"]["template_name"]

        template_dir = load_test_data(template_name, data_path)
        params_template = format_template(template_dir, template_name)

        # running workflow
        segment_pnh = create_full_T1_ants_subpipes(
            params=params, params_template=params_template,
            name="test_create_full_ants_subpipes_all_default_params")

        segment_pnh.base_dir = data_path

        segment_pnh.write_graph(graph2use="colored")
        assert op.exists(
            op.join(data_path,
                    "test_create_full_ants_subpipes_all_default_params",
                    "graph.png"))


def test_create_full_spm_subpipes_all_default_params():

    import os
    import json

    softs = ["spm"]
    all_species = ["macaque", 'baboon']
    spaces = ["native", "template"]

    for soft, species, space in product(softs, all_species, spaces):

        print("*** Testing soft {} with species {}".format(soft, species))

        wf_dir = (cwd / "workflows").resolve()
        print(wf_dir)

        params_file = os.path.join(wf_dir,  "params_segment_{}_{}.json".format(
            species, soft))

        assert op.exists(params_file), \
            "Could not find params_file {}".format(params_file)

        params = json.load(open(params_file))

        # params template
        template_name = params["general"]["template_name"]

        template_dir = load_test_data(template_name, data_path)
        params_template = format_template(template_dir, template_name)

        # running workflow
        segment_pnh = create_full_spm_subpipes(
            params=params, params_template=params_template, space=space,
            name="test_create_full_ants_subpipes_all_default_params")

        segment_pnh.base_dir = data_path

        segment_pnh.write_graph(graph2use="colored")
        assert op.exists(
            op.join(data_path,
                    "test_create_full_ants_subpipes_all_default_params",
                    "graph.png"))


if __name__ == '__main__':

    test_create_full_spm_subpipes_all_default_params()
    test_create_full_ants_subpipes_all_default_params()
    test_create_full_ants_t1_subpipes_all_default_params()
