# coding=utf-8
import config

import logging as _logging

_logging.basicConfig(level=config.LOGGING_LEVEL,
                     format='[%(asctime)s]: %(levelname)s %(message)s',
                     datefmt='%Y-%m-%d %H:%M:%S')

logger = _logging.getLogger()
