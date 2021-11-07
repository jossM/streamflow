from typing import Optional, List
from unittest.mock import AsyncMock, call

import pytest

from db.tasks import TASK_KEY_PREFIX
from db.db_model import DbTask


@pytest.fixture
def scan_table_mock(mocker):
    async_mock = AsyncMock()
    mocker.patch("db.tasks._scan_table", side_effect=async_mock)
    return async_mock


def make_scan_table_response(results: Optional[List[DbTask]] = None, next_key: Optional[str] = None) -> dict:
    if results is None:
        results = []
    return {'Items': [dict(id=TASK_KEY_PREFIX+t.id, **t.dict(exclude_defaults=True, exclude={"id"})) for t in results],
            "LastEvaluatedKey": next_key}


@pytest.fixture
def mock_task_lock(mocker):
    lock_mock = AsyncMock()
    acquire_lock_mock = AsyncMock()
    lock_mock.attach_mock(acquire_lock_mock, 'acquire_lock')
    release_lock_mock = AsyncMock()
    lock_mock.attach_mock(release_lock_mock, 'release_lock')
    mocker.patch("db.tasks.acquire_lock", side_effect=lock_mock.acquire_lock)
    mocker.patch("db.tasks.release_lock", side_effect=lock_mock.release_lock)
    return lock_mock


EXPECT_MOCK_CALLS = [call.acquire_lock(), call.release_lock()]


@pytest.fixture
def mock_update_db(mocker):
    update_mock = AsyncMock()
    mocker.patch('db.tasks.update_db', side_effect=update_mock)
    return update_mock
