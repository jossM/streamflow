import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

import backoff
import boto3
from botocore.exceptions import ClientError

import config
from logs import logger

kinesis = boto3.resource("kinesis") if not config.TEST_ENV else None


@backoff.on_exception(backoff.constant, ClientError, interval=1, max_time=10)
async def get_shard_ids() -> List[str]:
    """ List all shards of the """
    stream = await asyncio.to_thread(kinesis.describe_stream, StreamName=config.TASK_STREAM_NAME)
    try:
        return [shard["ShardId"] for shard in stream["StreamDescription"]["Shards"]]
    except KeyError:
        logger.error(f"Failed to parse kinesis response {stream}")
        raise


@backoff.on_exception(backoff.constant, ClientError, interval=1, max_time=10)
async def get_shard_iterator(shard_id: str, sequence_number: Optional[str] = None) -> str:
    """Retrieve a shard iterator in a shard starting"""
    kwargs = dict(
        StreamName=config.TASK_STREAM_NAME,
        ShardId=shard_id
    )
    if sequence_number is None:
        kwargs.update(ShardIteratorType="TRIM_HORIZON")
    else:
        kwargs.update(
            ShardIteratorType="AFTER_SEQUENCE_NUMBER",
            StartingSequenceNumber=sequence_number,
        )

    response = await asyncio.to_thread(
        kinesis.get_shard_iterator,
        StreamName=config.TASK_STREAM_NAME,
        ShardId=shard_id,
        ShardIteratorType="TRIM_HORIZON",
    )
    try:
        return response["ShardIterator"]
    except KeyError:
        logger.error(f"Failed to parse kinesis response {response}")
        raise


@dataclass(frozen=True)
class Record:
    """Represents a kinesis record"""
    sequence_number: str
    data: bytes
    partition_key: str
    timestamp: datetime


class ExpiredIterator(Exception):
    pass


@backoff.on_exception(backoff.constant, ClientError, interval=1, max_time=10)
async def get_records(shard_iterator: str) -> Tuple[List[Record], Optional[str]]:
    """Get record in the shard and the next shard iterator"""
    try:
        response = await asyncio.to_thread(
            kinesis.get_records,
            ShardIterator=shard_iterator
        )
    except ClientError as kinesis_error:
        try:
            if kinesis_error.response["Error"]["Code"] == "ExpiredIteratorException":
                raise ExpiredIterator("Iterator given as input was ")
        except KeyError:
            logger.error(f"Failed to parse kinesis error response {kinesis_error.response}")
        raise kinesis_error
    try:
        return [
            Record(
                sequence_number=record["SequenceNumber"],
                timestamp=record["ApproximateArrivalTimestamp"],
                data=record["Data"],
                partition_key=record["PartitionKey"]
            )
            for record in response['Records']
        ], response['NextShardIterator']
    except KeyError:
        logger.error(f"Failed to parse kinesis response {response}")
        raise