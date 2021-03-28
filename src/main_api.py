# coding=utf-8
"""
Used for local development
"""
import os

from api.app import flask_app
from config import CONFIG

if __name__ == "__main__":
    # todo: add configuration file for the app
    flask_app.run(host="0.0.0.0", port=os.getenv("STREAM_FLOW_PORT"), debug=CONFIG.flask_dev_mode)
