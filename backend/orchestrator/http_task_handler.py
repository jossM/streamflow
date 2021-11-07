import asyncio
import logging
import os

import backoff
from jinja2.sandbox import SandboxedEnvironment
import pydantic
from pydantic import BaseModel, Field
import requests
from typing import Optional, List, Union

import context_lib
from global_models.task_model import CallTask, HTTPServiceRequests
from orchestrator import cloudwatch_logs
from orchestrator.response_models import HTTPServiceRequests, Log
from task_queue.task_message_model import TaskTriggerMessage


class TaskTriggerResponse(BaseModel):
    """Response models expected from a service when a task is first requested"""
    next_logs_call: HTTPServiceRequests = Field(description="Arguments of the GET request for the following logs")
    cancel_call: HTTPServiceRequests = Field(description="Arguments of the PUT request for the following logs")


class NextLogsResponse(BaseModel):
    logs: List[Log] = Field(description="List of log level/log content pairs", default_factory=list)
    next_logs_call: HTTPServiceRequests = Field(description="Arguments of the GET request for the following logs")
    cancel_call_replacement: Optional[HTTPServiceRequests] = Field(
        description="Arguments of the DELETE request for the following logs", default=None
    )
    execution_succeeded: Optional[bool] = Field(description="Indicates whether the execution has been successful."
                                                            "If filled this will be the last call to get logs.")


async def handle_http_task(
        task_change: TaskTriggerMessage,
        task_interrupt_queue: asyncio.Queue,
        log_sender: Union[cloudwatch_logs.DummyLogSender, cloudwatch_logs.LogSender]) -> bool:
    """ Executing an http task and indicates back whether the execution was successful """

    logging.info(f"Task {task_change.task.id} starting on handler pid {os.getpid()}.")
    logging.getLogger("backoff").addHandler(log_sender)

    @backoff.on_exception(backoff.expo, requests.exceptions.HTTPError, max_tries=4)  # todo have retries in task def
    async def request_service(method: str, scheme: str, service_dns_or_ip: str, arguments: HTTPServiceRequests):
        response = await asyncio.to_thread(
            requests.request,
            method=method,
            url=f"{scheme}://{service_dns_or_ip}/{arguments.route}",
            data=arguments.body,
            headers=arguments.headers,
            cookies=arguments.cookies
        )
        try:
            response.raise_for_status()
        except requests.exceptions.RequestException:
            logging.warning(f"Failed to query service. {response.raw}")
            raise
        return response

    service_args = dict(
        scheme="https",  # todo: have scheme defined in service registry
        service_dns_or_ip="service_dns_or_ip"  # todo: have dns in service registry
    )

    # task trigger
    context = context_lib.Context(
        task_id=task_change.task.id,
        execution_id=task_change.execution_id,
        **task_change.execution_context.dict(exclude_defaults=True)
    )

    json_call_template = task_change.task.call_template.json(
        exclude_defaults=True,
        exclude=set(CallTask.schema()['properties']) - set(HTTPServiceRequests.schema()['properties']),
    )
    call_spec: CallTask = CallTask.parse_raw(SandboxedEnvironment().from_string(json_call_template).render(ctx=context))

    try:
        post_response = await request_service(
            method="POST",
            arguments=HTTPServiceRequests(

            ),  # todo: get this from task def
            **service_args
        )
    except requests.exceptions.HTTPError:
        logging.error("Failed to trigger the task")
        raise
    try:
        trigger_response = TaskTriggerResponse.parse_raw(post_response.raw)
    except pydantic.ValidationError:
        logging.error(f"Invalid response received from service when triggering the task. {post_response.raw}")
        raise
    cancel_args = trigger_response.cancel_call

    # Task running
    while True:

        # check up on task advancement
        get_response = await request_service(
            method="GET",
            argument=trigger_response.next_logs_call,
            **service_args
        )
        try:
            log_response = NextLogsResponse.parse_raw(get_response.raw)
        except pydantic.ValidationError:
            logging.error(f"Invalid response received from service when triggering the task. {get_response.raw}")
            raise
        await log_sender.send_service_logs(log_response.logs)
        if log_response.execution_succeeded is not None:
            return log_response.execution_succeeded
        if log_response.cancel_call_replacement is not None:
            cancel_args = log_response.cancel_call_replacement

        # handle cancellations from orchestrator
        if not task_interrupt_queue.empty():
            interruption_message = task_interrupt_queue.get()  # empty
            logging.warning(f"Sending cancel requests: {interruption_message}")
            await request_service(
                method="DELETE",
                arguments=cancel_args,
                **service_args
            )
            logging.info(f"Cancel requests acknowledged by service")
