from typing import Iterable

import backoff
from botocore.exceptions import ClientError

import config
from db.dynamodb import dynamodb
from logs import logger
from model.task_model import Task

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
