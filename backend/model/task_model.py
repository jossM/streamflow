"""
All models describing what a task is according to streamflow
"""
from typing import Any, Dict, List

from pydantic import BaseModel, Field, validator

# should be read from bottom to top


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
    pod: Any = Field(
        default=None,
        title="pod_template",
        description="The Jinja template of the pod that must be run by kubernetes",
    )
    call: CallTask = Field(
        default=None,
        title="call_template",
        description="The Jinja template of the HTTP call that must be performed"
    )

    next_tasks_ids: List[str] = Field(
        default_factory=list,
        title="Children_Tasks",
        description="List of all tasks ids that depend on this task"
    )

    @validator("pod", "call")
    def check_at_least_one(cls, all_templates):
        # pydantic.ValidationError will be raised at the end
        assert sum(template is None for template in all_templates) != 1, \
            "Exactly one of pod_template or call_template must be filled"
