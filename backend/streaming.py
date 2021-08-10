from typing import Iterable, Type, List
from itertools import islice

T = Type['T']


def group(stream: Iterable[T], group_size: int) -> Iterable[List[T]]:
    """ group elements together in batches of requested size """
    if group_size < 1:
        raise ValueError("group_size should be a strictly positive integer")
    generator = iter(stream)
    while True:
        single_group = list(islice(generator, group_size))
        if not single_group:
            return
        yield single_group
