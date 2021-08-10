from pytest import fixture

from model.db import DbTask
from db.tasks import _deserialize_downward_task, _serialize_downward_task


@fixture()
def initial_db_task():
    task = DbTask(
        id="dag/sample_task",
        pod_template="template",
    )
    return task


def test_serialisation(initial_db_task: DbTask):
    processed_db_tasks = _deserialize_downward_task(_serialize_downward_task(initial_db_task))
    assert processed_db_tasks == initial_db_task
