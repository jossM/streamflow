# coding=utf-8
import logging
import os
from typing import NamedTuple


class Config(NamedTuple):
    """ Full list of configuration option """
    streamflow_mode: str = os.getenv("STREAMFLOW_MODE", "production")
    flask_dev_mode: bool = False
    test_mode: bool = False
    api_prefix: str = os.getenv("STREAMFLOW_API_PREFIX", "")
    logging_level: str = os.getenv("STREAMFLOW_LOGGING_LEVEL", logging.INFO)
    api_secret_key: bytes = os.getenv("STREAMFLOW_API_SECRET_KEY", "").encode("utf-8")

    def replace(self, **kwargs) -> "Config":
        """ _replace wrapper that explicitly exposes named tuple method """
        # returns a new configuration based on a previous one
        return self._replace(**kwargs)
