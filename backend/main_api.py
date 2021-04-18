# coding=utf-8
"""
Used for local development
"""
import os

from api.streamflow import flask_app
import config

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=config.DEV_PORT, debug=config.FLASK_DEV_MODE)
