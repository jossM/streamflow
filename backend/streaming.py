from typing import Iterable, Type, List
from itertools import islice

T = Type['T']


def group(iterable_elements: Iterable[T], group_size: int) -> Iterable[List[T]]:
    """ group elements together in batches of requested size """
    generator = iter(iterable_elements)
    while True:
        single_group = list(islice(generator, group_size))
        if not single_group:
            return
        yield single_group
