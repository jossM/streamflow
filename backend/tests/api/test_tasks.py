from fastapi.testclient import TestClient
from pytest import fixture


from main_api import app
from api.tasks import ROUTE
from model.task_model import Task, CallTask


client = TestClient(app)


def make_task():
    return Task(
        id="dummy_dag/valid_task",
        call_templates=[
            CallTask(
                url_template="localhost",
                method="GET",
            )
        ],
    ).json()



def test_tasks_get(mocker):
    pass


def test_tasks_put():
    client.put(ROUTE, )


