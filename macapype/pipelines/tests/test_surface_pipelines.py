
import os.path as op

from macapype.utils.utils_tests import (make_tmp_dir, load_test_data,
                                        format_template)

from macapype.utils.misc import parse_key
from macapype.pipelines.surface import (create_nii_to_mesh_pipe)


data_path = make_tmp_dir()


def test_create_surface_pipe():

    # params
    params = {
        "nii_to_mesh_pipe":
        {
                "split_hemi_pipe":
                {
                },

        }
    }

    # params_template
    template_name = "haiko89_template"
    template_dir = load_test_data(template_name)

    params_template = format_template(template_dir, template_name)

    # running workflow
    segment_pnh = create_nii_to_mesh_pipe(
        params=parse_key(params, "nii_to_mesh_pipe"),
        params_template=params_template,
        name="nii_to_mesh_pipe")

    segment_pnh.base_dir = data_path

    segment_pnh.write_graph(graph2use="colored")
    assert op.exists(op.join(data_path,
                             "nii_to_mesh_pipe",
                             "graph.png"))
