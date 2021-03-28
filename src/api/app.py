# coding=utf-8
from flask import Flask as _Flask
from flask_restful import Api as _Api

from config import CONFIG as _CONFIG


flask_app = _Flask(__name__)
api = _Api(prefix=_CONFIG.api_prefix)

# all routes



api.init_app(flask_app)
