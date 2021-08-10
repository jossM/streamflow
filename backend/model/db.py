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
    tasks_to_update: List[DbTask] = Field(description="List of all task to be created or updated")

    def __len__(self):
        return len(self.ids_to_remove) + len(self.tasks_to_update)

    def __eq__(self, other: 'DbTasksChange'):
        if type(self) != type(other) or self.ids_to_remove != other.ids_to_remove:
            return False
        other_tasks_to_update = list(other.tasks_to_update)
        for task in self.tasks_to_update:
            try:
                other_tasks_to_update.pop(other_tasks_to_update.index(task))
            except ValueError:
                return False
        return len(other_tasks_to_update) == 0  # todo: add test
