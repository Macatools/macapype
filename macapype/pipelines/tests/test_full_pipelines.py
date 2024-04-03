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
        },
        "fast":
        {
        },
        "extract_pipe":
        {
        },
        "debias":
        {
        },
        "brain_segment_pipe":
        {
            "reg":
                {},
            "segment_atropos_pipe":
                {}
        }
    }

    # params template
    template_name = params["general"]["template_name"]

    template_dir = load_test_data(template_name, data_path)
    params_template = format_template(template_dir, template_name)

    # running workflow
    segment_pnh = create_full_ants_subpipes(
        params=params, params_template=params_template,
        params_template_stereo=params_template,
        name="test_create_full_ants_subpipes_no_args")

    segment_pnh.base_dir = data_path

    segment_pnh.write_graph(graph2use="colored")
    assert op.exists(
        op.join(data_path, "test_create_full_ants_subpipes_no_args",
                "graph.png"))


def test_create_full_ants_subpipes_all_default_params():

    import os
    import json

    softs = ["ants"]
    all_species = ["marmo", "macaque", 'baboon']
    spaces = ["native", "template"]
    pads = [True, False]

    for soft, species, space, pad in product(softs, all_species, spaces, pads):

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
            params_template_stereo=params_template,
            pad=pad,
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
    pads = [True, False]

    for soft, species, space, pad in product(softs, all_species, spaces, pads):

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
            params_template_stereo=params_template,
            pad=pad,
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
    pads = [True, False]

    for soft, species, space, pad in product(softs, all_species, spaces, pads):

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
            params=params, params_template=params_template,
            params_template_stereo=params_template, space=space,
            pad=pad,
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
