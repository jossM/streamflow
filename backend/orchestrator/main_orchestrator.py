import asyncio
import logging
from asyncio.subprocess import Process, create_subprocess_shell
from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path
import signal
from typing import Optional, Set, Iterable
from uuid import uuid4

import click

from logs import logger
from task_queue.task_message_model import TaskTriggerMessage
from task_queue import task_streaming
from utils.async_utils import close_loop_with_delay, StopSignal


_stop_signal = StopSignal()
loop = asyncio.get_event_loop()


@dataclass(frozen=True)
class TaskHandling:
    process: Process
    message_task: TaskTriggerMessage


async def _orchestrator_main(health_check_every_s: int):
    """Launches process that starts and stop tasks. And maintain task db state @ scale."""
    global _stop_signal
    orchestrator_id = str(uuid4())
    logger.info(f"Starting orchestrator {orchestrator_id}")

    task_event_stream = task_streaming.get_message_stream()
    running_tasks: Set[TaskHandling] = set()
    last_check: datetime = datetime.now()
    async for event in task_event_stream:  # infinite loop
        event: Optional[TaskTriggerMessage]

        if event is not None and not _stop_signal:
            running_tasks.add(await start_task(orchestrator_id=orchestrator_id, event=event))

        # started task handling
        done_tasks = set(task for task in running_tasks if task.process.returncode is not None)
        for task in done_tasks:
            await handle_done_task(task)
        running_tasks = running_tasks - done_tasks

        # scheduler load management
        if (datetime.now() - last_check).total_seconds() >= health_check_every_s:
            # todo: ensure this scheduler process will not get down scaled soon if not in local
            scheduler_will_get_downscaled = False
            if scheduler_will_get_downscaled:
                logger.info(f"Scheduler shutting down due to downscale")
                break
        if _stop_signal:
            for task in running_tasks:
                logger.info(f'Interrupting task "{task.message_task.task.id}"'
                            f', execution "{task.message_task.execution_id}"'
                            f', attempt {task.message_task.unique_key}')
                task.process.send_signal(signal.SIGINT)
            break
        break

    while running_tasks:
        try:
            done_task = next(task for task in running_tasks if task.process.returncode)
        except StopIteration:
            continue
        await handle_done_task(done_task)


async def start_task(orchestrator_id: str, event: TaskTriggerMessage) -> TaskHandling:
    """ Create a subprocess to handle the event """
    task_event_file_path = os.path.join(Path.home(), f"task_{event.unique_key}.json")
    with open(task_event_file_path) as file:
        file.write(event.task.json(exclude_defaults=True))

    command = f"python /local-src/cli.py orchestrator start-task --orchestrator_id {orchestrator_id} {task_event_file_path}"
    logging.info(f"launching subprocess of task {event.task.id} execution {event.execution_id} - attempt {event.unique_key} with : {command}")
    task_execution_environment = dict(os.environ)

    task_process = await create_subprocess_shell(command, env=task_execution_environment)
    asyncio.create_task(task_process.wait()).add_done_callback(lambda _: os.remove(task_event_file_path))
    return TaskHandling(
        process=task_process,
        message_task=event,
    )


async def handle_done_task(task_handling: TaskHandling) -> None:
    task_process = task_handling.process
    event = task_handling.message_task
    if task_process.returncode is None:
        raise ValueError('Task process is not done yet')
    if task_process.returncode == 0:
        logger.info(
            f"Process of task {event.task.id} execution {event.execution_id} - attempt {event.unique_key} succeeded"
        )
        return
    logger.error(f"Process of task {event.task.id} execution {event.execution_id} - attempt {event.unique_key} failed")
    while True:
        line_bytes = await task_process.stderr.readline()
        if not line_bytes:
            break
        logger.error(line_bytes.decode('utf8'))


def _shutdown(sig_name: str):
    """Cancels all running tasks after a given time"""
    global _stop_signal, loop
    logger.warning(f'Signal {sig_name} received. Scheduler is forcefully being shutdown.')
    _stop_signal.stop()
    loop.create_task(close_loop_with_delay(loop=loop, seconds_delay=5))  # todo: pass this in config


@click.command(help=_orchestrator_main.__doc__)
@click.option("--health_check_seconds",
              default=1,
              help="Time between each lifecycle check of the scheduler. Default : 1s")
def start(health_check_seconds):
    logger.info('Starting scheduler')
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGQUIT):
        loop.add_signal_handler(sig, _shutdown, sig.name)
    loop.run_until_complete(_orchestrator_main(health_check_seconds))
