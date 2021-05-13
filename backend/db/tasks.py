from typing import Iterable, List, Optional, Dict

import backoff
from botocore.exceptions import ClientError
from pydantic import ValidationError, BaseModel, Field

import config
from db.dynamodb import dynamodb
from model.pagination import serialize_token, deserialize_token
from model.task_model import Task
from logs import logger
import streaming


TASK_TABLE = dynamodb.Table(config.TASKS_TABLE) if not config.TEST_ENV else None


def _parse_item(item: Dict, do_raise: bool = True) -> Optional[Task]:
    """Dummy function to add logs to parsing errors """
    try:
        return Task(**item)
    except (ValidationError, TypeError):
        logger.error(f"Failed to parse item {item}")
        if do_raise:
            raise
        else:
            return None


@backoff.on_exception(backoff.constant, ClientError, interval=1, max_time=10)
def _scan_table(**kwargs):
    """Dummy function to add backoff logic to table scan"""
    return TASK_TABLE.scan(**kwargs)


@backoff.on_exception(backoff.constant, ClientError, interval=1, max_time=10)
def _batch_changes(max_25_tasks_list: List[Task]):
    """Dummy function to add backoff logic to table batch write"""
    if len(max_25_tasks_list):
        raise ValueError("Task cannot be changed more than 25 at a time")
    with TASK_TABLE.batch_writer() as batch:
        for task in max_25_tasks_list:
            batch.put_item(task.dict())


def get_all_tasks() -> Iterable[Task]:  # todo: add option to filter on a given dag or list of dags
    """ Get all tasks corresponding to filters"""
    start_key = None
    scan_args = dict(ProjectionExpression=', '.join(sorted(Task.__fields__)))
    while True:
        if start_key:
            scan_args.update(ExclusiveStartKey=start_key)
        response = _scan_table(**scan_args)
        for task_data in response.get('Items', []):
            task = _parse_item(task_data, do_raise=True)
            if task is not None:
                yield task
        start_key = response.get('LastEvaluatedKey')
        if start_key is None:
            break


def save_all_tasks(tasks: Iterable[Task]):
    for task_batch in streaming.group(tasks, 25):
        _batch_changes(task_batch)


class TasksPage(BaseModel):
    tasks: List[Task] = Field(title="Tasks", description="Tasks of the page")
    next_page_token: Optional[str] = Field(title="Page Token", description="Token to be given back "
                                                                 "to the api to get the next page")


def get_tasks_page(page_size=50,
                   page_token: Optional[str] = None,
                   filter_expression: Optional[str] = None) -> TasksPage:  # todo pass default page size in config
    """Store all tasks in dynamodb"""
    scan_args = dict(
        ProjectionExpression=', '.join(sorted(Task.__fields__)),
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
    response = _scan_table(**scan_args)
    start_key = response.get('LastEvaluatedKey')
    return TasksPage(
        tasks=[_parse_item(task_data) for task_data in response.get('Items', [])],
        next_page_token=serialize_token(start_key) if start_key else None,
    )
