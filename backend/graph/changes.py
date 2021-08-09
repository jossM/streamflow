from typing import List, Dict

from model.db import DbTasksChange, DbTask
from graph.utils import is_task_in_dag
from model.task_model import TasksChange


def build_db_changes(change: TasksChange, current_tasks: Dict[str, DbTask]) -> DbTasksChange:
    """Evaluate all changes that must be performed on task to apply the requested changes"""
    deleted_tasks_ids = (
        {task_id for task_id in current_tasks.keys() if is_task_in_dag(task_id, change.dags)}
        - {task.id for task in change.tasks}
    )
    new_tasks_mixed = change.tasks + [task for task in current_tasks.values()
                                      if not is_task_in_dag(task.id, change.dags)]
    new_tasks_db = [
        DbTask(
            **task.dict(exclude={"next_tasks_ids"}, exclude_unset=True),
            next_tasks_ids=sorted(other_task.id for other_task in new_tasks_mixed
                                  if task.id in other_task.previous_tasks_ids)
        )
        for task in new_tasks_mixed
    ]
    return DbTasksChange(
        tasks_to_update=sorted([task_db for task_db in new_tasks_db if task_db.id != current_tasks.get(task_db.id)],
                               key=lambda task: task.id),
        ids_to_remove=deleted_tasks_ids,)


def build_new_tasks_graph(change: DbTasksChange, current_tasks: Dict[str, DbTask]) -> List[DbTask]:
    """Create the new list of tasks effective after the DbChanges has been performed"""
    all_tasks: Dict[str, DbTask] = {task.id: task for task in current_tasks.values()
                                    if task.id not in change.ids_to_remove}
    all_tasks.update({task.id: task for task in change.tasks_to_update})
    return sorted(all_tasks.values(), key=lambda task: task.id)
