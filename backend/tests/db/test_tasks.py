from pytest import fixture

from db.db_model import DbTask
from db.tasks import _deserialize_downward_task, _serialize_downward_task
from global_models.task_model import CallTask


@fixture()
def initial_db_task():
    task = DbTask(
        id="dag/sample_task",
        call_template=CallTask(service="any_service", route="/"),
        max_execution_time=1,
        warn_execution_time_ratio=0.5,
    )
    return task


def test_serialisation(initial_db_task: DbTask):
    processed_db_tasks = _deserialize_downward_task(_serialize_downward_task(initial_db_task))
    assert processed_db_tasks == initial_db_task
