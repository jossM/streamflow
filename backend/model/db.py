from typing import List, Optional, Set

from pydantic import BaseModel, Field

from model.task_model import Task


class DbTask(Task):
    next_tasks_ids: List[str] = Field(
        default_factory=list,
        title="Children Tasks Ids",
        description="List of all tasks ids that depend on this task"
    )


class TasksPage(BaseModel):
    """ Represents a list of task to be returned as a page"""
    tasks: List[DbTask] = Field(title="Tasks", description="Tasks of the page")
    next_page_token: Optional[str] = Field(
        title="Page Token",
        description="Token to be given back to the api to get the next page"
    )


class DbTasksChange(BaseModel):
    ids_to_remove: Set[str] = Field(description="List of all task ids to be deleted.")
    task_to_update: List[DbTask] = Field(description="List of all task to be created or updated")

    def __len__(self):
        return len(self.ids_to_remove) + len(self.task_to_update)

