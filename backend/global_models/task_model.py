"""
All models describing what a task is according to streamflow
"""
import json
from typing import Optional, List

from pydantic import BaseModel, Field, validator, root_validator

from config import DAG_DELIMITER
from orchestrator.response_models import HTTPServiceRequests


class CallTask(HTTPServiceRequests):
    service: str = Field(
        title="Service",
        description="Service to be called for the task",
    )
    call_retry: int = Field(
        title="Call Retry",
        description="number of times each calls should be retried before giving up in the middle of a task",
        default=5
    )


# todo: define service here

class Task(BaseModel):
    id: str = Field(
        title="Task id",
        description="Uniquely identifies the task. \".\" element will serve to indicate dag(s) of the task",
        min_length=1,
        max_length=1000
    )

    max_execution_time: int = Field(
        description="Maximum number of seconds a task should run. If set to 0, corresponds to 3 times",
        gt=0,
        lt=3600*24,
    )

    warn_execution_time_ratio: float = Field(
        description="Amount of time after witch warning should be triggered for the task",
        gt=0,
        lt=1,
    )

    call_template: Optional[CallTask] = Field(
        default=None,
        description="The Jinja template of the HTTP call that must be performed",
    )

    previous_tasks_ids: List[str] = Field(
        default_factory=list,
        description="List of all this task depends on",
    )

    @validator("id")
    def _check_task_id(cls, task_id: str):
        # pydantic.ValidationError will be raised at the end so Exception type does not matter
        assert DAG_DELIMITER in task_id, \
            f'A task must always belong to a dag. A task should always contain one char "{DAG_DELIMITER}"'
        return task_id

    @root_validator
    def _check_at_least_one_template(cls, values):
        assert sum(bool(values.get(field)) for field in cls.__fields__ if "template" in field) == 1, \
            "Exactly one of pod_template or call_template must be filled"
        return values


class TasksChange(BaseModel):
    dags: List[str] = Field(
        title="Dags",
        description="List of fully identified dags for which the list of tasks should correspond.",
        min_size=1,
    )
    tasks: List[Task] = Field(
        title="Tasks",
        description="List of all the tasks that the new version of the dag should contain.",
    )

    @root_validator
    def _ensure_dags_supersedes_tasks_dags(cls, kwargs):
        dags: List[str] = kwargs.get('dags', [])
        tasks: List[Task] = kwargs.get('tasks', [])
        tasks_outside_of_dags = sorted(json.dumps(t.id) for t in tasks
                                       if not any(t.id.startswith(dag_name) for dag_name in dags))
        assert not tasks_outside_of_dags, \
            f"The following tasks are outside of edited dags {', '.join(tasks_outside_of_dags)}"
        return kwargs
