# coding=utf-8
import logging as _logging
import os as _os
from typing import Optional as _Opt


TEST_ENV = _os.getenv("STREAMFLOW.TEST_MODE", False)


def _get_os_env_variable(environment_key: str, default: _Opt[str] = None) -> str:
    environment_key = f"STREAMFLOW.{environment_key.upper()}"
    env_value = _os.getenv(environment_key, default)
    if env_value is None and default is None and not TEST_ENV:
        raise EnvironmentError(f'Required key {environment_key} is missing and has no default.')
    return env_value


LOGGING_LEVEL: str = getattr(_logging, _get_os_env_variable("LOGGING_LEVEL", "info").upper())
TASKS_TABLE: str = _get_os_env_variable("TASKS_TABLE_NAME")
TASKS_RUNS_TABLE: str = _get_os_env_variable("TASKS_RUNS_TABLE_NAME")
DAG_DELIMITER: str = _get_os_env_variable("DAG_DELIMITER_CHAR", "/")
TASK_STREAM_NAME: str = _get_os_env_variable("TASK_STREAM_NAME")
