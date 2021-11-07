from functools import cached_property, wraps
from typing import Optional, Any, Union

from datetime import datetime
from pydantic import BaseModel, Field

from utils.type_hint import UNSET, UnsetType


class CustomContext(BaseModel):
    execution_date: datetime = Field(
        description="Execution moment",
        default=UNSET,
    )
    last_execution: Optional[Union[UnsetType, datetime]] = Field(
        description="Last time the task was run. If None, task has never run.",
        default=UNSET,
    )
    last_successful_execution: Optional[Union[UnsetType, datetime]] = Field(
        description="Last time this task was successful. If None, task has never run.",
        default=UNSET,
    )


def _apply_override(method):
    @wraps(method)
    def _prop(obj_self: 'Context', *args, **kwargs):
        try:
            return obj_self.overridden_properties[method.__name__]
        except KeyError:
            return method(obj_self, *args, **kwargs)
    return _prop


class Context:
    def __init__(self, task_id: str, execution_date: datetime, execution_id: str, **overridden_properties: Any):
        self.execution_id = execution_id
        self.task_id = task_id
        self.execution_date = execution_date
        self._overridden_properties = overridden_properties

    @property
    def overridden_properties(self):
        return self._overridden_properties

    @cached_property
    @_apply_override
    def last_execution(self) -> Optional[datetime]:
        return  # todo look into database for this info

    @cached_property
    @_apply_override
    def last_successful_execution(self) -> Optional[datetime]:
        return  # todo


