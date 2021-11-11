import asyncio
from logs import logger


async def close_loop_with_delay(loop, seconds_delay):
    """Closes the loop after a given amount of time"""
    if seconds_delay > 0:
        logger.warning(f"Preparing to shutdown in a maximum of {seconds_delay} second(s)")
        await asyncio.sleep(seconds_delay)
    logger.info(f"Shutting down loop")
    loop.stop()
