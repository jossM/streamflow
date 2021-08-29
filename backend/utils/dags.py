from typing import Union

from config import DAG_DELIMITER
from db.db_model import DbTask
from global_models.task_model import Task


def get_task_dag(task: Union[Task, DbTask], dag_level: int):
    """Get the dag in which a task belongs"""
    tasks_dags = task.id.split(DAG_DELIMITER)
    return DAG_DELIMITER.join(tasks_dags[:min(dag_level+1, len(tasks_dags)-1)])