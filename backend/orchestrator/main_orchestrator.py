import asyncio
import queue
import time
from asyncio.subprocess import Process
from dataclasses import dataclass
from datetime import datetime
import signal
from typing import Dict, Optional

import click

from logs import logger
from task_queue.task_message_model import TaskTriggerMessage
from task_queue import task_streaming
from utils.async_utils import close_loop_with_delay


stop = False
loop = asyncio.get_event_loop()


@dataclass(frozen=True)
class TaskHandling:
    process: Process
    message_task: TaskTriggerMessage


async def _orchestrator_main(health_check_every_s: int):
    """Launches process that starts and stop tasks. And maintain task db state @ scale."""
    global stop
    task_event_stream = task_streaming.get_message_stream()
    running_tasks: Dict[str, TaskHandling] = {}
    last_check: Optional[datetime] = None
    async for event in task_event_stream:  # infinite loop
        # scheduler load management
        if stop:
            break
        if last_check is None or (datetime.now() - last_check).total_seconds() >= health_check_every_s:

            # todo: ensure this scheduler process will not get down scaled soon if not in local
            scheduler_will_get_downscaled = False
            if scheduler_will_get_downscaled:
                logger.info(f"Scheduler shutting down due to downscale")
                break
            scheduler_should_keep_polling = True
            if not scheduler_should_keep_polling:
                await asyncio.sleep(1)
                continue

        # task handling
        if event is None:  # no new messages.
            await asyncio.sleep(1)
            continue
        pass  # todo handle messages in subprocess here

    if running_tasks:
        logger.info(
            "Waiting for the end of the following tasks:"
            + ', '.join(['{} run {'.format(task_handling.message_task.task.id)
                         for task_handling in running_tasks.values()])
        )
        await asyncio.gather(*[task_handling.process.wait() for task_handling in running_tasks.values()])


def _shutdown(sig_name: str):
    """Cancels all running tasks after a given time"""
    global stop, loop
    logger.warning(f'Signal {sig_name} received. Scheduler is forcefully being shutdown.')
    stop = True
    loop.create_task(close_loop_with_delay(loop=loop, seconds_delay=3))


@click.command(help=_orchestrator_main.__doc__)
@click.option("--health_check_seconds",
              default=1,
              help="Time between each lifecycle check of the scheduler. Default : 1s")
def start(health_check_seconds):
    logger.info('Starting scheduler')
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGQUIT):
        loop.add_signal_handler(sig, _shutdown, sig.name)
    loop.run_until_complete(_orchestrator_main(health_check_seconds))
