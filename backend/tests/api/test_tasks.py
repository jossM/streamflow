from fastapi.testclient import TestClient

from main_api import app
from api.tasks import ROUTE
from model.db import TasksPage, DbTasksChange, Task
from model.task_model import TasksChange
from tests.model.utils import make_task, make_task_db
from tests.db.mocked_tasks import *


client = TestClient(app)
dag = 'random_dag_name'


def test_get_empty_tasks(scan_table_mock):
    scan_table_mock.return_value = make_scan_table_response(results=[])
    response = client.get(ROUTE)
    assert response.status_code == 200
    assert response.json() == TasksPage(tasks=[], next_page_token=None).dict()


def test_put_valid_object_in_empty_dag(scan_table_mock, mock_task_lock, mock_update_db: AsyncMock):
    scan_table_mock.return_value = make_scan_table_response(results=[])
    task = make_task(id=f'{dag}/task')
    put_response = client.put(ROUTE, TasksChange(dags=[dag], tasks=[task]).json(exclude_unset=True))
    assert put_response.status_code == 200, put_response.json()
    assert mock_task_lock.mock_calls == EXPECT_MOCK_CALLS
    mock_update_db.assert_awaited_once_with(DbTasksChange(
        ids_to_remove=set(),
        tasks_to_update=[DbTask(next_tasks_ids=[], **task.dict())]
    ))


def test_put_task_outside_of_dag(scan_table_mock, mock_task_lock, mock_update_db: AsyncMock):
    scan_table_mock.return_value = make_scan_table_response(results=[])
    task = make_task(id=f'other_{dag}/task')
    put_response = client.put(ROUTE, TasksChange.construct(dags=[dag], tasks=[task]).json(exclude_unset=True))
    assert put_response.status_code == 422, put_response.json()
    assert mock_task_lock.mock_calls == []
    mock_update_db.assert_not_awaited()


def test_put_update_tasks_in_dag(scan_table_mock, mock_task_lock, mock_update_db: AsyncMock):
    initial_task_id, new_task_id = (f"{dag}/initial_task", f"{dag}/new_task")
    scan_table_mock.return_value = make_scan_table_response(results=[make_task_db(id=f"{dag}/initial_task")])
    new_task = make_task(id=new_task_id)
    put_response = client.put(ROUTE, TasksChange(dags=[dag], tasks=[new_task]).json(exclude_unset=True))
    assert put_response.status_code == 200, put_response.json()
    assert mock_task_lock.mock_calls == EXPECT_MOCK_CALLS
    mock_update_db.assert_awaited_once_with(DbTasksChange(
        ids_to_remove={initial_task_id},
        tasks_to_update=[DbTask(**new_task.dict(exclude_unset=True))]
    ))


def test_put_delete_dag(scan_table_mock, mock_task_lock, mock_update_db: AsyncMock):
    existing_task = make_task_db(id=f"{dag}/task_id")
    scan_table_mock.return_value = make_scan_table_response(results=[existing_task])
    put_response = client.put(ROUTE, TasksChange(dags=[dag], tasks=[]).json(exclude_unset=True))
    assert put_response.status_code == 200, put_response.json()
    assert mock_task_lock.mock_calls == EXPECT_MOCK_CALLS
    mock_update_db.assert_awaited_once_with(DbTasksChange(
        ids_to_remove={existing_task.id},
        tasks_to_update=[]
    ))


def test_put_delete_non_existent_dag(scan_table_mock, mock_task_lock, mock_update_db: AsyncMock):
    scan_table_mock.return_value = make_scan_table_response(results=[])
    put_response = client.put(ROUTE, TasksChange.construct(dags=["non_existent_dag"], tasks=[]).json(exclude_unset=True))
    assert put_response.status_code == 200, put_response.json()
    assert mock_task_lock.mock_calls == EXPECT_MOCK_CALLS
    mock_update_db.assert_not_awaited()


def test_delete_tasks_that_has_downstream(scan_table_mock, mock_task_lock, mock_update_db: AsyncMock):
    upstream_dag = f"upstream_dag"
    upstream_task_id = f"{upstream_dag}/task"
    downstream_task_id = f"{dag}/downstream_task"
    existing_tasks = [
        make_task_db(id=upstream_task_id, next_tasks_ids=[downstream_task_id]),
        make_task_db(id=downstream_task_id, previous_tasks_ids=[upstream_task_id]),
    ]
    scan_table_mock.return_value = make_scan_table_response(results=existing_tasks)
    put_response = client.put(ROUTE, TasksChange(dags=[upstream_dag], tasks=[]).json(exclude_unset=True))
    assert mock_task_lock.mock_calls == EXPECT_MOCK_CALLS
    assert put_response.status_code == 400, put_response.json()
    mock_update_db.assert_not_awaited()


def test_put_add_downstream_task(scan_table_mock, mock_task_lock, mock_update_db: AsyncMock):
    upstream_task_id = f"upstream_dag/task"
    existing_db_task = make_task_db(id=upstream_task_id, next_tasks_ids=[])

    scan_table_mock.return_value = make_scan_table_response(results=[existing_db_task])
    new_downstream_task = make_task(id=f"{dag}/downstream_task", previous_tasks_ids=[upstream_task_id])
    put_response = client.put(ROUTE, TasksChange(dags=[dag], tasks=[new_downstream_task]).json(exclude_unset=True))
    assert mock_task_lock.mock_calls == EXPECT_MOCK_CALLS
    assert put_response.status_code == 200, put_response.json()
    mock_update_db.assert_awaited_once_with(DbTasksChange(
        ids_to_remove=set(),
        tasks_to_update=[
            DbTask(**new_downstream_task.dict()),
            DbTask(
                **existing_db_task.dict(exclude_unset=True, exclude={"next_tasks_ids"}),
                next_tasks_ids=[new_downstream_task.id]
            ),
        ]
    ))


def test_put_task_with_invalid_upstream_task(scan_table_mock, mock_task_lock, mock_update_db: AsyncMock):
    scan_table_mock.return_value = make_scan_table_response(results=[])
    task = make_task(id=f"{dag}/task", previous_tasks_ids=[f"other_{dag}/non_existant_task"])
    put_response = client.put(ROUTE, TasksChange(dags=[dag], tasks=[task]).json(exclude_unset=True))
    assert mock_task_lock.mock_calls == EXPECT_MOCK_CALLS
    assert put_response.status_code == 400, put_response.json()
    mock_update_db.assert_not_awaited()


def test_put_circular_task(scan_table_mock, mock_task_lock, mock_update_db: AsyncMock):
    scan_table_mock.return_value = make_scan_table_response(results=[])
    task_id = f"{dag}/circular_task"
    task = make_task(id=task_id, previous_tasks_ids=[task_id])
    put_response = client.put(ROUTE, TasksChange(dags=[dag], tasks=[task]).json(exclude_unset=True))
    assert mock_task_lock.mock_calls == EXPECT_MOCK_CALLS
    assert put_response.status_code == 400, put_response.json()
    mock_update_db.assert_not_awaited()


def test_add_circular_link_between_tasks(scan_table_mock, mock_task_lock, mock_update_db: AsyncMock):
    upstream_task_id = f"{dag}/taskA"
    downstream_task_id = f"dagB/taskB"
    upstream_task_db = make_task_db(id=upstream_task_id, next_tasks_ids=[downstream_task_id])
    existing_tasks = [upstream_task_db, make_task_db(id=downstream_task_id, previous_tasks_ids=[upstream_task_id])]
    scan_table_mock.return_value = make_scan_table_response(results=existing_tasks)
    new_upstream_task = Task(
        **upstream_task_db.dict(exclude={"next_tasks_ids", "previous_tasks_ids"}),
        previous_tasks_ids=[downstream_task_id])  # this will introduce a cycle
    put_response = client.put(ROUTE, TasksChange(dags=[dag], tasks=[new_upstream_task]).json(exclude_unset=True))
    assert mock_task_lock.mock_calls == EXPECT_MOCK_CALLS
    assert put_response.status_code == 400, put_response.json()
    mock_update_db.assert_not_awaited()
