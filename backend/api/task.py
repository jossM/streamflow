from fastapi import FastAPI
from typing import List

from db.tasks import get_all_tasks, save_all_tasks
from model.task_model import Task


def add_tasks_resources(app: FastAPI):
    """Adds all resources for /tasks resources"""
    route = "/all_tasks"

    @app.get(route)
    def get() -> List[Task]:  # todo: add pagination
        return list(get_all_tasks())

    @app.post(route)
    def post(all_tasks: List[Task]) -> str:
        save_all_tasks(all_tasks)
        return f"Successfully registered {len(all_tasks)} task(s)"
