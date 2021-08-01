from fastapi.testclient import TestClient

from main_api import app
from api.tasks import ROUTE
from model.db import TasksPage, DbTasksChange, DbTask
from model.task_model import TasksChange
from tests.model.utils import make_task
from tests.db.mocked_tasks import *


client = TestClient(app)


def test_get_empty_tasks(scan_table_mock):
    scan_table_mock.return_value = make_scan_table_response(results=[])
    response = client.get(ROUTE)
    assert response.status_code == 200
    assert response.json() == TasksPage(tasks=[], next_page_token=None).dict()


def test_put_valid_object_in_empty_dag(scan_table_mock, mock_task_lock, mock_update_db: AsyncMock):
    scan_table_mock.return_value = make_scan_table_response(results=[])
    dag = 'random_dag_name'
    task = make_task(id=f'{dag}/task')
    put_response = client.put(ROUTE, TasksChange(dags=[dag], tasks=[task]).json(exclude_unset=True))
    assert put_response.status_code == 200, put_response.text
    assert mock_task_lock.mock_calls == EXPECT_MOCK_CALLS
    mock_update_db.assert_awaited_once_with(DbTasksChange(
        ids_to_remove=set(),
        task_to_update=[DbTask(next_tasks_ids=[], **task.dict())]
    ))
