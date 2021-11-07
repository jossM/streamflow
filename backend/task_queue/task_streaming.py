from dataclasses import dataclass
from typing import Iterator, Dict, List, Optional

from logs import logger
from task_queue import kinesis_stream
from task_queue.task_message_model import TaskTriggerMessage, ReadRecord, deserialize_message, serialize_message
from utils.shuffle import random_shuffle


@dataclass
class _ShardAdvancement:
    """Represents a kinesis record"""
    shard_iterator: str
    sequence_number: str


async def get_message_stream() -> Iterator[Optional[TaskTriggerMessage]]:
    """Orchestrating function to get records from the kinesis stream."""
    shard_advancement: Dict[str, _ShardAdvancement] = dict()
    while True:
        all_shard_ids = await kinesis_stream.get_shard_ids()
        for deleted_shard_id in set(shard_advancement.keys()) - set(all_shard_ids):
            shard_advancement.pop(deleted_shard_id)
        for shard_id in random_shuffle(all_shard_ids):
            records = None
            if shard_id in shard_advancement:
                try:
                    records, next_shard_iterator = await kinesis_stream.get_shard_records(shard_iterator=shard_id)
                except kinesis_stream.ExpiredIterator:
                    logger.info(f'Regenerating shard iterator for shard {shard_id}.')
                    shard_iterator = kinesis_stream.get_shard_iterator(
                        shard_id=shard_id,
                        sequence_number=shard_advancement[shard_id].sequence_number
                    )
            else:
                shard_iterator = kinesis_stream.get_shard_iterator(
                    shard_id=shard_id,
                    sequence_number=shard_advancement[shard_id].sequence_number
                )
            records: Optional[List[ReadRecord]]
            if records is None:
                # shard_iterator is always defined in this case
                # noinspection PyUnboundLocalVariable
                records, next_shard_iterator = await kinesis_stream.get_shard_records(shard_iterator)
            if not records:
                yield None
                continue
            for r in records:
                yield deserialize_message(r)
            # noinspection PyUnboundLocalVariable
            shard_advancement[shard_id].shard_iterator = next_shard_iterator
            shard_advancement[shard_id].sequence_number = records[-1].sequence_number


async def push_message(message: TaskTriggerMessage):
    pass  # todo:
