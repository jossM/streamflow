from typing import Optional, List, Tuple, Union

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from graph.changes import build_db_changes, build_new_tasks_graph
from graph.validation import get_orphan_tasks, get_tasks_cycles
from db import tasks as tasks_db
from model.db import TasksPage
from model.task_model import TasksChange

ROUTE = "/tasks"


class CyclesIntroduced(Exception):
    def __init__(self, message: str, cycles: List[List[str]]):
        self.message = message
        self.cycles = cycles


class InconsistentTasksDependencies(Exception):
    def __init__(self, message: str, inconsistent_links: List[Tuple[List[str], str]]):
        self.message = message
        self.inconsistent_links = inconsistent_links


def add_tasks_resources(app: FastAPI):
    """Adds all resources for /tasks resources"""

    @app.get(ROUTE, response_model=TasksPage)
    async def get(limit: int = 50, page_token: Optional[str] = None) -> TasksPage:
        # todo add right handling
        return await tasks_db.get_tasks_page(limit, page_token=page_token)

    @app.put(ROUTE, response_model=str)  # todo add documentation of errors
    async def put(tasks_change: TasksChange) -> str:
        # todo add right handling
        await tasks_db.acquire_lock()
        try:
            current_tasks = [task async for task in tasks_db.get_all_tasks()]
            db_changes = build_db_changes(current_tasks=current_tasks, change=tasks_change)
            if not db_changes.task_to_update or db_changes.ids_to_remove:
                return "No changes to perform."
            new_tasks_graph = build_new_tasks_graph(change=db_changes, current_tasks=current_tasks)
            orphan_tasks = get_orphan_tasks(new_tasks_graph)
            if orphan_tasks:
                raise InconsistentTasksDependencies(
                    message=f"Changes introduced inconsistent {len(orphan_tasks)} task(s) dependencies.",
                    inconsistent_links=[(orphan.previous_tasks_ids, orphan.id) for orphan in orphan_tasks]
                )
            tasks_cycle = get_tasks_cycles(new_tasks_graph)
            if tasks_cycle:
                raise CyclesIntroduced(
                    message=f"Modification would create {len(tasks_cycle)} tasks cycle(s).",
                    cycles=[[task.id for task in cycle] for cycle in tasks_cycle],
                )
            await tasks_db.update_db(db_changes)
        finally:
            await tasks_db.release_lock()
        return f"Deleted task(s) :{db_changes.ids_to_remove}" \
               f"\nUpdated tasks :{[task.id for task in db_changes.task_to_update]}"

    @app.exception_handler(CyclesIntroduced)
    async def handle_put_error(request: Request, exception: Union[CyclesIntroduced, InconsistentTasksDependencies]):
        exception_data = {"error_type": type(exception).__name__}
        exception_data.update({attr: getattr(exception, attr) for attr in dir(exception)})
        return JSONResponse(status_code=400, content=exception_data)

    app.exception_handler(CyclesIntroduced)(handle_put_error)
    app.exception_handler(InconsistentTasksDependencies)(handle_put_error)
