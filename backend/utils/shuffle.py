from random import shuffle
from typing import Type, List

T = Type['T']


def random_shuffle(elements: List[T]) -> List[T]:
    """Returns a the input lists in a random order"""
    elements_copy = list(elements)
    shuffle(elements_copy)
    return elements_copy