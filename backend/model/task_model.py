"""
All models describing what a task is according to streamflow
"""
import json
from typing import Optional, List, Tuple

from pydantic import BaseModel, Field, validator, root_validator

from config import DAG_DELIMITER


class CallTask(BaseModel):
    url_template: str = Field(
        title="Url",
        description="The Jinja formatted url template that needs to will be called"
    )
    method: str = Field(
        title="Method to call the api",
        description=""
    )

    response_name: Optional[str] = Field(
        title="Call_name",
        description="Name of the response data",
        default=None,
        min_length=1,
        max_length=150,
    )
    log_response: bool = Field(
        title="Log response",
        description="Whether the response data can be logged or not.",
        default=False,
    )
    template: str = Field(
        title="Step Arguments",
        description="jinja template returning the json object corresponding to requests arguments.",
        default="",
        max_length=10000,
    )


class Task(BaseModel):
    id: str = Field(title="Task id",
                    description="Uniquely identifies the task. \".\" element will serve to indicate dag(s) of the task",
                    min_length=1,
                    max_length=1000)

    pod_template: Optional[str] = Field(
        default=None,
        title="pod_template",
        description="The Jinja template of the pod that must be run by kubernetes",
    )

    call_templates: Optional[List[CallTask]] = Field(
        default=None,
        title="call_template",
        description="The Jinja template of the HTTP call that must be performed",
        min_items=1,
        max_items=10,
    )

    previous_tasks_ids: List[str] = Field(
        default_factory=list,
        title="Parent Tasks Ids",
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
        assert bool(values.get("call_templates")) + bool(values.get("pod_template")) == 1, \
            "Exactly one of pod_template or call_template must be filled"
        return values


class DbTask(Task):
    next_tasks_ids: List[str] = Field(
        default_factory=list,
        title="Children Tasks Ids",
        description="List of all tasks ids that depend on this task"
    )


class TasksChange(BaseModel):
    dags: List[str] = Field(
        title="Dags",
        description="List of fully identified dags for which the list of tasks should correspond.",
        min_size=1,)
    tasks: List[Task] = Field(
        title="Tasks",
        description="List of all the tasks that the new version of the dag should contain."
    )

    @validator("dags", "tasks")
    def ensure_dags_supersedes_tasks_dags(cls, args: Tuple[List[str], List[Task]]):
        dags, tasks = args
        tasks_outside_of_dags = sorted(json.dumps(t.id) for t in tasks
                                       if not any(t.id.startswith(dag_name) for dag_name in dags))
        assert not tasks_outside_of_dags, \
            f"The following tasks are outside of edited dags {', '.join(tasks_outside_of_dags)}"
