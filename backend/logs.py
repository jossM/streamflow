# coding=utf-8
from config import CONFIG
import os

import logging as _logging

_logging.basicConfig(level=CONFIG.logging_level,
                     format='[%(asctime)s]: {} %(levelname)s %(message)s'.format(os.getpid()),
                     datefmt='%Y-%m-%d %H:%M:%S')

logger = _logging.getLogger()