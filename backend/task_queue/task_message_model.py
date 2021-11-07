from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
from typing import Optional

from pydantic import BaseModel, Field, validator

from global_models.task_model import Task
from orchestrator.context_lib import CustomContext


class EventType(str, Enum):
    START = "START"
    CANCEL = "CANCEL"
    END = "END"


class TaskTriggerMessage(BaseModel):  # todo: move this in global models
    event_type: EventType
    execution_id: str
    execution_context: CustomContext
    task: Task
    reason: Optional[str] = None  # for log purpose only
    unique_key: Optional[str] = Field(description="Uniquely identifies the task message. Should not contain any space."
                                                  "Filled when the message is read only.",
                                      min_length=1,
                                      max_length=200,
                                      default=None)

    @validator("unique_key")
    def unique_key_does_not_contain_space(cls, v):
        if v is not None and " " in v:
            raise ValueError("must not contain space")
        return v


@dataclass(frozen=True)
class WrittenRecord:
    """Represents a kinesis record"""
    data: bytes
    partition_key: str


@dataclass(frozen=True)
class ReadRecord(WrittenRecord):
    sequence_number: str
    timestamp: datetime


def serialize_message(message: TaskTriggerMessage) -> WrittenRecord:
    return WrittenRecord(
        data=message.json(exclude_defaults=True, exclude={"unique_key", "moment"}).encode('utf8'),
        partition_key=message.execution_id,
    )


def deserialize_message(record: ReadRecord) -> TaskTriggerMessage:
    data = json.loads(record.data.decode("utf8"))  # todo: handle format error here
    [data.pop(key, None) for key in {"moment", "unique_key"}]
    return TaskTriggerMessage(
        **data,
        moment=record.timestamp,
        unique_key=f"{record.partition_key}_{record.sequence_number}"
    )
