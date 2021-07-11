from typing import Optional
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def scan_table_mock(mocker):
    async_mock = AsyncMock()
    mocker.patch("db.tasks._scan_table", side_effect=async_mock)
    return async_mock


def make_scan_table_response(results=None, next_key: Optional[str]=None) -> dict:
    if results is None:
        results = []
    return {'Items': results, "LastEvaluatedKey": next_key}
