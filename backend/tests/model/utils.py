from itertools import permutations
from typing import List, Set
from unittest.mock import call

from model.db import DbTask, DbTasksChange
from model.task_model import Task


def make_task(id='dag/id', **kwargs) -> Task:
    if not any(key.endswith("template") for key in kwargs.keys()):
        kwargs["pod_template"] = "template"
    return Task.construct(id=id, **kwargs)


def make_task_dict(**kwargs) -> dict:
    return make_task(**kwargs).dict(exclude_defaults=True)


def make_task_db(id='dag/id', **kwargs) -> DbTask:
    if not any(key.endswith("template") for key in kwargs.keys()):
        kwargs["pod_template"] = "template"
    return DbTask(id=id, **kwargs)
