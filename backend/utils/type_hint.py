from enum import Enum


class UnsetType(Enum):
    """ Dummy type to complement None value"""
    UNSET = 'UNSET'


UNSET = UnsetType.UNSET
