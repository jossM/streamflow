import logging
from enum import Enum
from typing import Dict
from datetime import datetime

from pydantic import BaseModel, Field


class HTTPServiceRequests(BaseModel):
    route: str = Field(description="Route to call on the service", min_length=1, max_length=2048)
    headers: Dict[str, str] = Field(description="Headers to pass for the next call", default_factory=dict)
    body: str = Field(description="Body to be sent along with the request", default="", max_length=2**20)  # i.e 1MB
    cookies: Dict[str, str] = Field(description="Cookies to be sent along with the request", default_factory=dict)


class LogLevel(Enum):
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTSET = logging.NOTSET


class Log(BaseModel):
    timestamp: datetime = Field(description="Moment the log was produced")
    log_level: LogLevel
    message: str
