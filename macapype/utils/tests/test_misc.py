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
