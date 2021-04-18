# coding=utf-8
from flask import Flask as _Flask
from flask_restful import Api as _Api

import config
from logs import logger
from api.task import Tasks

flask_app = _Flask(__name__)
api = _Api(prefix=config.API_PREFIX)

# all routes
api.add_resource(Tasks, Tasks.route)


api.init_app(flask_app)

if config.STREAMFLOW_MODE == config.StreamflowMode.DEV:
    logger.warning("Using development mode.")
