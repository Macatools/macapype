
from macapype.utils.utils_bids import create_datasink


def test_create_datasink_sub_ses():
    iterables = [('subject', "mysub"), ('session', 'myses')]
    datasink = create_datasink(iterables)
    print(datasink)

    assert True


def test_create_datasink_sub():
    iterables = [('subject', "mysub")]
    datasink = create_datasink(iterables)
    print(datasink)

    assert True
