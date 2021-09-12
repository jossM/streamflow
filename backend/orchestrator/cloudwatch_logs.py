import asyncio
from collections import deque
from datetime import datetime
import logging
from operator import attrgetter
from typing import List, Optional, Callable
from traceback import format_exc

import backoff
import boto3
from botocore.exceptions import ClientError
from logging import StreamHandler

import config
from utils import streaming
from orchestrator.response_models import Log, LogLevel

if config.CLOUDWATCH_LOG_GROUP:
    cloudwatch_client = boto3.client('logs')
else:
    logging.warning("Logs not persisted in cloudwatch")
    cloudwatch_client = None


def make_stream_name(unique_exec_key: str):
    return f"exec_{unique_exec_key}"


class LogSender(StreamHandler):
    """ Log handler able to reconciliate timestamp between server time and local time for async links"""

    def __init__(self, log_group: str, stream_name: str, log_formatter: Callable[[Log], str]):
        """
        :param stream_name: streamname in the cloud watch loggroup logs will be pushed to
        """
        super().__init__()
        self.log_group = log_group
        self.stream_name = stream_name
        self._local_log_queue = deque()
        self._sequence_token: Optional[str] = None

        _local_logger = logging.getLogger(f"cloudwatchLogger-{self.log_group}-{self.stream_name}")
        _local_logger.setLevel(logging.INFO)
        _local_file_handler = logging.FileHandler(f'./cloudwatchSendLog-{self.log_group}-{self.stream_name}.txt')
        _local_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        _local_logger.addHandler(_local_file_handler)
        can_fail_log_formatter = log_formatter

        def log_formatter(log: Log):
            # noinspection PyBroadException
            try:
                return can_fail_log_formatter(log)
            except Exception:
                _local_logger.error(format_exc())  # this special logger avoids infinite loop on errors
                return log.json(exclude={'timestamp'})[1:-1] + " (Failed formatting)"

        self.log_formatter = log_formatter

    def emit(self, record):  # handles local logs
        self._local_log_queue.append(
            Log(
                timestamp=datetime.now(),
                log_level=LogLevel[record.levelname],
                message=self.format(record)
            )
        )

    @backoff.on_exception(backoff.constant, ClientError, interval=0)
    async def _send_log_batch(self, logs: List[Log]):
        """ Sends a list of logs to cloudwatch """
        try:
            return await asyncio.to_thread(
                cloudwatch_client.put_log_events,
                logGroupName=config.CLOUDWATCH_LOG_GROUP,
                logStreamName=self.stream_name,
                logEvents=[
                    dict(
                        timestamp=single_log.timestamp.timestamp(),
                        message=self.log_formatter(single_log)
                    )
                    for single_log in logs
                ]
            )
        except (cloudwatch_client.exceptions.DataAlreadyAcceptedException,
                cloudwatch_client.exceptions.InvalidSequenceTokenException) as e:
            next_sequence_token = e.response["Error"]["Message"].split()[-1]
            if next_sequence_token == "null":
                self._sequence_token = None
            else:
                self._sequence_token = next_sequence_token
            raise
        except cloudwatch_client.exceptions.ResourceNotFoundException:
            await asyncio.to_thread(
                cloudwatch_client.create_log_group,
                logGroupName=self.log_group,
                logStreamName=self.stream_name,
            )
            logging.info(f"Stream name {self.stream_name} in group {self.log_group} created")
            raise

    async def send_service_logs(self, service_logs: List[Log]) -> None:
        """ Sends all logs from service and local buffered logs in a time increasing order"""
        if not service_logs:
            logging.debug("no log to send for this call")
            return
        timestamp = attrgetter("timestamp")
        max_service_timestamp = max(service_logs, key=timestamp)
        logs_to_send = deque(service_logs)
        logs_to_send.extend(filter(lambda log: log.timestamp <= max_service_timestamp, self._local_log_queue))
        for log_batch in streaming.group(sorted(logs_to_send, key=timestamp), 10000):
            await self._send_log_batch(log_batch)

    def flush(self) -> None:
        for log_batch in streaming.group(sorted(self._local_log_queue, key=attrgetter("timestamp")), 10000):
            await self._send_log_batch(log_batch)
