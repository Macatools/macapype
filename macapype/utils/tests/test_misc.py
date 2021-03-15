from nipype.interfaces.base import traits

from macapype.utils.misc import parse_key


def test_parse_key_empty():
    params = {}

    val = parse_key(params, "test")
    assert not val


def test_parse_key_Undefined():
    params = traits.Undefined

    val = parse_key(params, "test")
    assert not val


def test_split_indexed_mask():

    from macapype.utils.utils_tests import load_test_data, format_template
    from macapype.utils.misc import split_indexed_mask

    template_name = "NMT_v2.0_asym"
    nmt_dir = load_test_data(name=template_name)
    params_template = format_template(nmt_dir, template_name)

    list_split_files = split_indexed_mask(params_template["template_seg"])

    assert len(list_split_files) != 0
