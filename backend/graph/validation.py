from typing import List, Dict, Set

from networkx import simple_cycles, DiGraph

from db.db_model import DbTask


def get_orphan_tasks(all_tasks: List[DbTask]) -> List[DbTask]:
    """List all orphans tasks if the change is applied to the current state"""
    tasks_ids: Set[str] = {task.id for task in all_tasks}
    orphans = [
        DbTask(**task.dict(exclude={"previous_tasks_ids"}),
               previous_tasks_ids=[parent_id for parent_id in task.previous_tasks_ids if parent_id not in tasks_ids])
        for task in all_tasks if not all(parent_id in tasks_ids for parent_id in task.previous_tasks_ids)
    ]
    return sorted(orphans, key=lambda o: o.id)


def get_tasks_cycles(all_tasks: List[DbTask]) -> List[List[DbTask]]:
    """List all cycles if the change is applied to the current state"""
    tasks_map: Dict[str, DbTask] = {task.id: task for task in all_tasks}
    dag = DiGraph(
        [(task.id, downstream_task_id) for task in all_tasks for downstream_task_id in task.next_tasks_ids]
    )
    all_cycles = list(simple_cycles(dag))
    return [[tasks_map[task_id] for task_id in cycle] for cycle in all_cycles]
