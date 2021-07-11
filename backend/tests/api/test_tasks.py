from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from main_api import app
from api.tasks import ROUTE, TasksPage
from model.task_model import Task, CallTask
from tests.model.utils import make_task_dict
from tests.db.test_mocked_tasks import *


client = TestClient(app)


def test_get_empty_tasks(scan_table_mock: AsyncMock):
    scan_table_mock.return_value = make_scan_table_response(results=[])
    response = client.get(ROUTE)
    assert response.status_code == 200
    assert response.json() == TasksPage(tasks=[], next_page_token=None).dict()


def test_tasks_put():  # todo
    #  client.put(ROUTE, )
    pass

