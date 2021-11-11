import asyncio
import logging
import signal

import click

import config
from logs import logger
from orchestrator import cloudwatch_logs
from orchestrator.http_task_handler import handle_http_task
from task_queue.task_message_model import TaskTriggerMessage
from utils.async_utils import build_shutdown_callback


@start_cmd.command(name="task")  # todo
@click.argument('task_json', type=click.STRING, help="json respecting the TaskTriggerMessage formatting.")
@click.option('--orchestrator_id', type=click.STRING, help="Id of the scheduler for observability.")
@click.option("--no-orchestrator", is_flag=True, help="Required if orchestrator id isn't filled")
def handle_task_cmd(task_json: str, orchestrator_id: str = None, no_orchestrator: bool = False):
    task_change: TaskTriggerMessage = TaskTriggerMessage.parse_raw(task_json)

    def log_formatter(log: cloudwatch_logs.Log):
        return "{log_level} - {message}".format(**log.dict())  # todo: make the log format configurable

    if config.CLOUDWATCH_LOG_GROUP:
        log_sender = cloudwatch_logs.LogSender(
            log_group=config.CLOUDWATCH_LOG_GROUP,
            stream_name=cloudwatch_logs.make_stream_name(task_change.unique_key),
            log_formatter=log_formatter,
        )
        logger.addHandler(log_sender)
    else:
        log_sender = cloudwatch_logs.DummyLogSender(log_formatter=log_formatter)

    if not no_orchestrator and orchestrator_id is None:
        raise click.Abort("Missing orchestrator_id while in production. Cannot launch task.")
    elif orchestrator_id is not None:
        logging.info(f"Handling task change {task_change.unique_key} on orchestrator {orchestrator_id}")
    loop = asyncio.get_event_loop()
    task_interrupt_queue = asyncio.Queue()
    loop.add_signal_handler(signal.SIGINT, build_shutdown_callback(
        loop=loop,
        max_shutdown_seconds=task_change.task.max_execution_time,
        task_interrupt_queue=task_interrupt_queue
    ))

    # todo: handle other types of tasks here
    try:
        loop.run_until_complete(handle_http_task(
            task_change=task_change,
            task_interrupt_queue=task_interrupt_queue,
            log_sender=log_sender,
        ))
        logging.info(f"Successfully run task {task_change.unique_key} on orchestrator {orchestrator_id}")
    finally:
        loop.close()
