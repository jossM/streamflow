# coding=utf-8
import logging as _logging
import os as _os
from typing import Optional as _Opt
from enum import Enum as _Enum


def _get_os_env_variable(environment_key: str, default: _Opt[str] = None) -> str:
    environment_key = f"STREAMFLOW.{environment_key.upper()}"
    env_value = _os.getenv(environment_key, default)
    if env_value is None and default is None:
        raise EnvironmentError(f'Required key {environment_key} is missing and has no default.')
    return env_value


class StreamflowMode(_Enum):
    PRODUCTION = "production"
    DEV = "dev"
    TEST = "test"


_STREAMFLOW_MODE = _get_os_env_variable("MODE", "PRODUCTION").upper()
try:
    STREAMFLOW_MODE: StreamflowMode = StreamflowMode[_STREAMFLOW_MODE]
except KeyError:
    raise EnvironmentError(f'Required key STREAMFLOW.MODE has invalid value {_STREAMFLOW_MODE}.')
FLASK_DEV_MODE: bool = (STREAMFLOW_MODE == StreamflowMode.DEV)
TEST_MODE: bool = (STREAMFLOW_MODE == StreamflowMode.TEST)
DEV_PORT: str = _get_os_env_variable("PORT", "8080")
API_PREFIX: str = _get_os_env_variable(f"API_PREFIX", "")
LOGGING_LEVEL: str = getattr(_logging, _get_os_env_variable(f"LOGGING_LEVEL", "info").upper())
API_SECRET_KEY: bytes = _get_os_env_variable(f"API_SECRET_KEY", "").encode("utf-8")
TASKS_TABLE: str = _get_os_env_variable(f"TASKS_TABLE_NAME")
TASKS_RUNS_TABLE: str = _get_os_env_variable(f"TASKS_RUNS_TABLE_NAME")
