# coding=utf-8

import logging
from os import getenv as _getenv

from .base import Config as _Config

CONFIG: _Config
_MODE_ENV_VAR_NAME = "STREAMFLOW_MODE"
_STREAMFLOW_MODE = _getenv(_MODE_ENV_VAR_NAME, "")
logging.info(f'Retrieved streamflow mode from env: "{_MODE_ENV_VAR_NAME}"={_STREAMFLOW_MODE}')
_STREAMFLOW_MODE = _STREAMFLOW_MODE.lower()
if _STREAMFLOW_MODE == "dev":
    logging.warning(f'Using dev mode.')
    from .dev import make_dev_config
    CONFIG = make_dev_config(streamflow_mode=_STREAMFLOW_MODE)
elif _STREAMFLOW_MODE == "test":
    from .test import make_test_config
    logging.info(f'Using test mode.')
    CONFIG = make_test_config(streamflow_mode=_STREAMFLOW_MODE)
else:
    CONFIG = _Config(streamflow_mode=_STREAMFLOW_MODE)
