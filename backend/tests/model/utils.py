from model.task_model import Task
from model.db import DbTask


def make_task(id='dag/id', **kwargs) -> Task:
    if not kwargs:
        kwargs["pod_template"] = "template"
    return Task.construct(id=id, **kwargs)


def make_task_dict(**kwargs) -> dict:
    return make_task(**kwargs).dict(exclude_defaults=True)


def make_task_db(id='dag/id', **kwargs) -> DbTask:
    if not kwargs:
        kwargs["pod_template"] = "template"
    return DbTask(id=id, **kwargs)
