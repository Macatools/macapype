# from .binary_fill_holes import BinaryFillHoles


def test_BinaryFillHoles():

    """
    TODO
    """
    # val = BinaryFillHoles()
    assert True
    pass


def test_split_indexed_mask():

    from macapype.utils.utils_tests import load_test_data, format_template
    from macapype.nodes.segment import split_indexed_mask

    template_name = "NMT_v2.0_asym"
    nmt_dir = load_test_data(name=template_name)
    params_template = format_template(nmt_dir, template_name)

    list_split_files = split_indexed_mask(params_template["template_seg"])

    assert len(list_split_files) != 0


def test_copy_header():
    assert True
    pass
