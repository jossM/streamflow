# coding=utf-8
from fastapi import FastAPI

from api.task import add_tasks_resources

app = FastAPI()

# all routes
add_tasks_resources(app)
