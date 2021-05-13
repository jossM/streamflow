from pytest import fixture, raises

from streaming import group


@fixture
def list_stream():
    return list(range(3))


def test_group(list_stream):
    assert list(group(list_stream, len(list_stream)-1)) == [list_stream[:-1], [list_stream[-1]]]


def test_group_empty_stream():
    assert list(group(stream=[], group_size=1)) == []


def test_group_end_corresponds_to_stream_end(list_stream):
    assert list(group(list_stream, len(list_stream))) == [list_stream]


def test_group_with_bad_size_arg(list_stream):
    with raises(ValueError):
        list(group(list_stream, group_size=0))
