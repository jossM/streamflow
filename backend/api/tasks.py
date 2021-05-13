from typing import Optional

from fastapi import FastAPI

from db.tasks import get_tasks_page, save_all_tasks, TasksPage
from model.task_model import TasksChange

ROUTE = "/tasks"


def add_tasks_resources(app: FastAPI):
    """Adds all resources for /tasks resources"""

    @app.get(ROUTE, response_model=TasksPage)
    def get(limit: int = 50, page_token: Optional[str] = None) -> TasksPage:  # todo: add async handling
        # todo add right handling
        return get_tasks_page(limit, page_token=page_token)

    @app.put(ROUTE, response_model=str)
    def put(tasks_change: TasksChange) -> str:
        # todo add right handling
        save_all_tasks(tasks_change.tasks)
        return f"Successfully registered {len(tasks_change.tasks)} task(s)"
