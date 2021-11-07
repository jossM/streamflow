import asyncio
from asyncio.subprocess import Process
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

import click

from logs import logger
from task_queue.task_message_model import TaskTriggerMessage
from task_queue import task_streaming


@dataclass(frozen=True)
class TaskHandling:
    process: Process
    message_task: TaskTriggerMessage


async def _orchestrator_main(health_check_every_s: int):
    """Start and stop tasks. And maintain db state @ scale."""
    task_event_stream = task_streaming.get_message_stream()
    running_tasks: Dict[str, TaskHandling] = {}
    last_check: Optional[datetime] = None
    while True:
        # scheduler load management
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
        event = next(task_event_stream)
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


@click.command()
def start():
    asyncio.run(_orchestrator_main())
