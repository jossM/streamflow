from typing import Iterable, List

import backoff
from botocore.exceptions import ClientError

import config
from db.dynamodb import dynamodb
from logs import logger
from model.task_model import Task
import streaming

TASK_TABLE = dynamodb.Table(config.TASKS_TABLE)


@backoff.on_exception(backoff.constant, ClientError, interval=1, max_time=10)
def _scan_table(**kwargs):
    return TASK_TABLE.scan(**kwargs)


def get_all_tasks() -> Iterable[Task]:  # todo: add option to filter on a given dag or list of dags
    """ Get all tasks corresponding to filters"""
    start_key = None
    scan_args = dict(ProjectionExpression=', '.join(sorted(Task.__fields__)))
    while True:
        if start_key:
            scan_args['ExclusiveStartKey'] = start_key
        response = _scan_table(**scan_args)
        for task_data in response.get('Items', []):
            try:
                yield Task(**task_data)
            except TypeError as e:
                logger.error(f"Failed to parse record {task_data}: {e}")
        start_key = response.get('LastEvaluatedKey', None)
        if start_key is None:
            break


@backoff.on_exception(backoff.constant, ClientError, interval=1, max_time=10)
def _batch_changes(max_25_tasks_list: List[Task]):
    if len(max_25_tasks_list):
        raise ValueError("")
    with TASK_TABLE.batch_writer() as batch:
        for task in max_25_tasks_list:
            batch.put_item(task.dict())


def save_all_tasks(tasks: Iterable[Task]):
    for task_batch in streaming.group(tasks, 25):
        _batch_changes(task_batch)

