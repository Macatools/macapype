
from macapype.utils.utils_bids import create_datasink


def test_create_datasink():
    iterables = [('subjects', "mysub"), ('sessions', 'myses')]
    datasink = create_datasink(iterables)

    print(datasink)

    assert True
