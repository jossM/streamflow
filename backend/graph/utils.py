from typing import List

from model.task_model import Task


def is_task_in_dag(task_id: str, dags: List[str]) -> bool:
    """Indicates whether a given task is in a list of dag ids"""
    return any(task_id.startswith(dag) for dag in dags)
