import asyncio
import signal

import click

import config
from logs import logger
from orchestrator import cloudwatch_logs
from orchestrator.http_task_handler import handle_http_task
from task_queue.task_message_model import TaskTriggerMessage
from utils.async_utils import StopSignal, close_loop_with_delay

_loop = asyncio.get_event_loop()
_stop_signal = StopSignal()


def _shutdown(sig_name: str):
    """Cancels all running tasks after a given time"""
    global _stop_signal, _loop
    logger.warning(f'Signal {sig_name} received. Scheduler is forcefully being shutdown.')
    _stop_signal.stop()
    _loop.create_task(close_loop_with_delay(loop=_loop, seconds_delay=3))  # todo: pass this in config


@click.command(name="start-task")
@click.argument('task_json', type=click.Path, help="path to the local json file with the TaskTriggerMessage.")
@click.option('--orchestrator_id', type=click.STRING, help="Id of the scheduler for observability.", required=True)
def start_task(task_json: str, orchestrator_id: str = None):
    """Call an external service to perform the task"""
    global _loop, _stop_signal
    task_change: TaskTriggerMessage = TaskTriggerMessage.parse_raw(task_json)  # todo ensure crash here are displayed in orchestrator logs

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

    logger.info(f"Handling task change {task_change.unique_key} on orchestrator {orchestrator_id}")
    _loop.add_signal_handler(signal.SIGINT, _shutdown, "SIGINT")

    # todo: handle other types of tasks here
    try:
        _loop.run_until_complete(handle_http_task(
            task_change=task_change,
            stop_signal=_stop_signal,
            log_sender=log_sender,
        ))
        logger.info(f"Successfully run task {task_change.unique_key} on orchestrator {orchestrator_id}")
    finally:
        _loop.close()
