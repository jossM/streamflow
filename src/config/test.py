# coding=utf-8
from .base import Config as _Config


def make_test_config(streamflow_mode: str) -> _Config:
    return _Config(
        streamflow_mode=streamflow_mode,
        flask_dev_mode=True,
        test_mode=True
    )