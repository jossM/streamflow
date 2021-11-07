from typing import List

from db.db_model import DbTask
from global_models.task_model import Task, TasksChange, CallTask


def make_task(id='dag/id', max_execution_time=1, warn_execution_time_ratio=.7, **kwargs) -> Task:
    if not any(key.endswith("template") for key in kwargs.keys()):
        kwargs["call_template"] = CallTask(service="any_service", route="/")
    return Task.construct(
        id=id,
        max_execution_time=max_execution_time,
        warn_execution_time_ratio=warn_execution_time_ratio,
        **kwargs
    )


def make_task_dict(**kwargs) -> dict:
    return make_task(**kwargs).dict(exclude_defaults=True)


def make_task_db(id='dag/id', max_execution_time=1, warn_execution_time_ratio=.7, **kwargs) -> DbTask:
    if not any(key.endswith("template") for key in kwargs.keys()):
        kwargs["call_template"] = CallTask(service="any_service", route="/")
    return DbTask(
        id=id,
        max_execution_time=max_execution_time,
        warn_execution_time_ratio=warn_execution_time_ratio,
        **kwargs
    )


def make_task_change_json(dags: List[str], tasks: List[Task]):
    return TasksChange.construct(dags=dags, tasks=tasks).json(exclude_unset=True)
