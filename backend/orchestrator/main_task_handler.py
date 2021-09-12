import asyncio
import logging
import signal
from typing import Callable

import click

import config
from orchestrator import cloudwatch_logs
from orchestrator.http_task_handler import handle_http_task
from orchestrator.main_orchestrator import start_cmd
from task_queue.task_message_model import TaskChangeMessage


def build_shutdown_callback(loop: asyncio.AbstractEventLoop,
                            max_shutdown_seconds: int,
                            task_interrupt_queue: asyncio.Queue) -> Callable:
    """Cancels all running tasks after a given time"""
    def shutdown(sig):
        logging.warning(f'Signal {sig.name} received.')
        task_interrupt_queue.put(f"Task must stop due to signal {sig.name} received..")
        if max_shutdown_seconds > 0:
            logging.info(f"Preparing to shutdown in a maximum of {max_shutdown_seconds} second(s)")
            await asyncio.sleep(delay=max_shutdown_seconds)
        loop.stop()
    return shutdown


@start_cmd.command(name="task")
@click.argument('task_json', type=click.STRING, help="json respecting the TaskChangeMessage formatting.")
@click.option('--orchestrator_id', type=click.STRING, help="Id of the scheduler for observability.")
@click.option("--no-orchestrator", is_flag=True, help="Required if orchestrator id isn't filled")
def handle_task_cmd(task_json: str, orchestrator_id: str = None, no_orchestrator: bool = False):
    task_change = TaskChangeMessage.parse_raw(task_json)

    def log_formatter(log: cloudwatch_logs.Log):
        return f"{log.log_level} - {log.message}"  # todo make this configurable

    if config.CLOUDWATCH_LOG_GROUP:
        log_sender = cloudwatch_logs.LogSender(
            log_group=config.CLOUDWATCH_LOG_GROUP,
            stream_name=cloudwatch_logs.make_stream_name(task_change.unique_key),
            log_formatter=log_formatter,
        )
        logging.getLogger().addHandler(log_sender)
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
        max_shutdown_seconds=1,  # todo replace max_shutdown here
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
