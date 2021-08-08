from collections import defaultdict
from typing import List, Set, Dict, Optional

from model.db import DbTasksChange, DbTask
from graph.utils import is_task_in_dag
from model.task_model import TasksChange


def _get_deleted_tasks_ids(change: TasksChange, current_tasks: List[DbTask]) -> Set[str]:
    """ list all tasks that must be deleted for the input change """
    return (
        {task.id for task in current_tasks if is_task_in_dag(task, change.dags)}
        - {task.id for task in change.tasks}
    )


def _get_tasks_updated_in_dag(change: TasksChange, current_tasks: List[DbTask]):
    """ list all tasks that must be updated to perform the change """
    previous_tasks = {task.id: task for task in current_tasks}
    updated_tasks_dependency: Dict[str, Set[str]] = defaultdict(set)
    for task in change.tasks:
        for parent_task_id in task.previous_tasks_ids:
            updated_tasks_dependency[parent_task_id].add(task.id)
    potential_content_updated_tasks = [
        DbTask(**task.dict(exclude={"next_tasks_ids"}),
               next_tasks_ids=sorted(updated_tasks_dependency[task.id]))
        for task in change.tasks
    ]
    return list(filter(lambda task: task != previous_tasks.get(task.id), potential_content_updated_tasks))


def _get_next_tasks_ids_updates(current_tasks: List[DbTask],
                                updated_tasks: Optional[List[DbTask]] = None,
                                deleted_ids: Optional[Set[str]] = None):
    """List all the tasks changes that must be changed to apply the relevant task edition / suppression"""
    updated_tasks_map: Dict[str, DbTask]
    if updated_tasks is None:
        updated_tasks_map = {}
    else:
        updated_tasks_map = {task.id: task for task in updated_tasks}
    if deleted_ids is None:
        deleted_ids = set()
    current_tasks_map: Dict[str, DbTask] = {task.id: task for task in current_tasks}
    edited_task_ids = deleted_ids | set(updated_tasks_map.keys())
    affected_upstream_ids = set()
    for task_id in edited_task_ids:
        if task_id not in current_tasks_map and task_id not in deleted_ids:
            new_previous_tasks_ids = set(updated_tasks_map[task_id].previous_tasks_ids)
            all_possible_tasks_ids = set(updated_tasks_map.keys()) | set(current_tasks_map.keys())
            affected_upstream_ids.update(new_previous_tasks_ids & all_possible_tasks_ids - edited_task_ids)
            continue
        if task_id in deleted_ids:
            remaining_previous_task_ids = set()
        else:
            remaining_previous_task_ids = set(updated_tasks_map[task_id].previous_tasks_ids)
        affected_upstream_ids.update(set(current_tasks_map[task_id].previous_tasks_ids) - remaining_previous_task_ids)
    return [
        DbTask(
            **current_tasks_map[task_id].dict(exclude={"next_tasks_ids"}),
            next_tasks_ids=sorted(
                {task_id for task_id in current_tasks_map[task_id].next_tasks_ids
                 if task_id not in edited_task_ids}
                | {task.id for task in updated_tasks
                   if current_tasks_map[task_id].id in task.previous_tasks_ids}
            )
        )
        for task_id in affected_upstream_ids
    ]


def build_db_changes(change: TasksChange, current_tasks: List[DbTask]) -> DbTasksChange:
    """Evaluate all changes that must be performed on task to apply the requested changes"""
    deleted_tasks_ids = _get_deleted_tasks_ids(current_tasks=current_tasks, change=change)
    content_updated_tasks = _get_tasks_updated_in_dag(current_tasks=current_tasks, change=change)
    graph_updated_tasks = _get_next_tasks_ids_updates(current_tasks=current_tasks,
                                                      deleted_ids=deleted_tasks_ids,
                                                      updated_tasks=content_updated_tasks)
    change = DbTasksChange(
        tasks_to_update=sorted(content_updated_tasks + graph_updated_tasks, key=lambda task: task.id),
        ids_to_remove=deleted_tasks_ids,
    )
    return change


def build_new_tasks_graph(change: DbTasksChange, current_tasks: List[DbTask]) -> List[DbTask]:
    """Create the new list of tasks effective after the DbChanges has been performed"""
    all_tasks: Dict[str, DbTask] = {task.id: task for task in current_tasks if task.id not in change.ids_to_remove}
    all_tasks.update({task.id: task for task in change.tasks_to_update})
    return sorted(all_tasks.values(), key=lambda task: task.id)
