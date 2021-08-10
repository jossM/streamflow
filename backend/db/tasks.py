import itertools
from typing import AsyncIterable, Optional, Dict
import asyncio

import backoff
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from pydantic import ValidationError

import config
from db.dynamodb import dynamodb
from model.db import TasksPage, DbTasksChange, DbTask
from model.pagination import serialize_token, deserialize_token
from logs import logger
import streaming

TASK_TABLE = dynamodb.Table(config.TASKS_TABLE) if not config.TEST_ENV else None
LOCK_TASK_ID = "TASK_LOCK"  # todo use this as env config variable
TASK_KEY_PREFIX = "TASK-"
assert not LOCK_TASK_ID.startswith(TASK_KEY_PREFIX), \
    f'Invalid config : LOCK_TASK_ID "{LOCK_TASK_ID}" begins with TASK_KEY_PREFIX "{TASK_KEY_PREFIX}"'


# Lock
@backoff.on_exception(backoff.constant, ClientError, interval=1, max_time=10)
async def acquire_lock():
    """ Gets the lock on the tasks table to ensure tasks checks are ok for a given modification"""
    await asyncio.to_thread(
        TASK_TABLE.put_item,
        Item={'id': LOCK_TASK_ID}, ConditionExpression='attribute_not_exists(id)'
    )


@backoff.on_exception(backoff.constant, ClientError, interval=1, max_time=10)
async def release_lock():
    """ Gets the lock on the tasks table to ensure tasks checks are ok"""
    await asyncio.to_thread(TASK_TABLE.delete_item, Key={'id': LOCK_TASK_ID})


# Utils
def _deserialize_downward_task(item: Dict, do_raise: bool = True) -> Optional[DbTask]:
    """
    Transforms a dynamodb item into a DownTask
    :raises if the  key has a bad format
    """
    try:
        clean_item = dict(item)
        clean_item["id"] = item["id"][len(TASK_KEY_PREFIX):]
        return DbTask(**clean_item)
    except (ValidationError, TypeError, KeyError):
        logger.error(f"Failed to parse item {item}")
        if do_raise:
            raise
        else:
            return None


def _serialize_downward_task(task: DbTask) -> Dict:
    """Transforms a DownTask into a dynamodb item."""
    item = task.dict(exclude={"id"}, exclude_defaults=True)
    item.update(id=TASK_KEY_PREFIX + task.id)
    return item


# read
@backoff.on_exception(backoff.constant, ClientError, interval=1, max_time=10)
async def _scan_table(**kwargs):
    """Dummy function to add backoff logic to table scan"""
    return await asyncio.to_thread(TASK_TABLE.scan, **kwargs)


async def get_all_tasks() -> AsyncIterable[DbTask]:  # todo: add option to filter on a given dag or list of dags
    """ Get all tasks corresponding to filters"""
    start_key = None
    scan_args = dict(
        ProjectionExpression=', '.join(sorted(DbTask.__fields__)),
        KeyConditionExpression=Key('id').begins_with(TASK_KEY_PREFIX)
    )
    while True:
        if start_key:
            scan_args.update(ExclusiveStartKey=start_key)
        response = await _scan_table(**scan_args)
        for task_data in response.get('Items', []):
            task = _deserialize_downward_task(task_data, do_raise=True)
            if task is not None:
                yield task
        start_key = response.get('LastEvaluatedKey')
        if start_key is None:
            break


async def get_tasks_page(page_size: int = 50,  # todo pass default page size in config
                         page_token: Optional[str] = None,
                         filter_expression: Optional[str] = None) -> TasksPage:
    """Store all tasks in dynamodb"""
    scan_args = dict(
        ProjectionExpression=', '.join(sorted(DbTask.__fields__)),
        Limit=page_size,
    )

    if page_token is not None:
        parsed_token = deserialize_token(page_token)
        scan_args.update(ExclusiveStartKey=parsed_token.start_key)
        scan_args.update(FilterExpression=parsed_token.filters)
        if filter_expression is not None and filter_expression != parsed_token.filters:
            logger.warn("filter_expression has been passed along with page_token and will be ignored")
    elif filter_expression is not None:
        scan_args.update(FilterExpression=filter_expression)
    response = await _scan_table(**scan_args)
    next_key = response.get('LastEvaluatedKey')
    return TasksPage(
        tasks=[_deserialize_downward_task(task_data) for task_data in response.get('Items', [])],
        next_page_token=serialize_token(next_key) if next_key else None,
    )


# Updates


@backoff.on_exception(backoff.constant, ClientError, interval=1, max_time=10)
async def _batch_changes(tasks_list: DbTasksChange):
    """Dummy function to add backoff & async logic to table batch write"""
    await asyncio.to_thread(_sync_batch_changes, tasks_list)


def _sync_batch_changes(tasks_list: DbTasksChange):
    """Dummy function to perform the write in db"""
    with TASK_TABLE.batch_writer() as batch:
        for task in tasks_list.tasks_to_update:
            batch.put_item(Item=_serialize_downward_task(task))
        for task_id in tasks_list.ids_to_remove:
            batch.delete_item(Key={"id": task_id})


async def update_db(db_changes: DbTasksChange) -> None:
    all_change_batches = streaming.group(
        itertools.chain(db_changes.tasks_to_update, db_changes.ids_to_remove),
        25  # dynamodb does not support more than 25 elements in a batch call at the moment
    )
    for change_batch_elements in all_change_batches:
        task_change_batch = DbTasksChange(
            tasks_to_update=[update for update in change_batch_elements if isinstance(update, DbTask)],
            ids_to_remove={deletion for deletion in change_batch_elements if isinstance(deletion, str)},
        )
        await _batch_changes(task_change_batch)
