"""
All models describing what a task is according to streamflow
"""
import json
from typing import Optional, Dict, List, Tuple

from pydantic import BaseModel, Field, validator

from config import DAG_DELIMITER


class CallTask(BaseModel):
    setup_arguments: List[Dict] = Field(  # todo: handle this part
        default_factory=list,
        title="Step Arguments",
        description="All arguments to call the function defined with STREAMFLOW.CALL_ENV_SETUP "
                    "to set up environment to be injected in template",
    )
    template: str = Field(
        title="Step Arguments",
        description="jinja template returning the json object corresponding to requests arguments.",
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
    call_template: Optional[CallTask] = Field(
        default=None,
        title="call_template",
        description="The Jinja template of the HTTP call that must be performed"
    )

    next_tasks_ids: List[str] = Field(
        default_factory=list,
        title="Children_Tasks",
        description="List of all tasks ids that depend on this task"
    )

    @validator("pod_template", "call_template")
    def check_at_least_one(cls, all_templates):
        # pydantic.ValidationError will be raised at the end so Exception type does not matter
        assert sum(template is None for template in all_templates) != 1, \
            "Exactly one of pod_template or call_template must be filled"

    @validator("id")
    def check_task_id(cls, task_id: str):
        assert DAG_DELIMITER in task_id, \
            f'A task must always belong to a dag. A task should always contain one char "{DAG_DELIMITER}"'


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
