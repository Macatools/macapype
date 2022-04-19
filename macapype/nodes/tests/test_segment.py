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


def test_fill_list_vol():

    from macapype.utils.utils_tests import load_test_data, format_template
    from macapype.nodes.segment import fill_list_vol

    import nibabel as nib

    template_name = "MBM_v3.0.1"
    nmt_dir = load_test_data(name=template_name)
    params_template = format_template(nmt_dir, template_name)

    nb_classes = 5
    vol_3c = [params_template["template_gm"],
              params_template["template_wm"],
              params_template["template_csf"]]

    vol_5c = fill_list_vol(vol_3c, nb_classes)

    first_vol_shape = nib.load(vol_5c[0]).get_fdata().shape
    last_vol_shape = nib.load(vol_5c[-1]).get_fdata().shape

    assert len(vol_5c) == nb_classes

    assert first_vol_shape == last_vol_shape


if __name__ == '__main__':
    test_fill_list_vol()
