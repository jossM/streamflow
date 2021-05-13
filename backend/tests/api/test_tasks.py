from typing import Optional

from fastapi.testclient import TestClient

from main_api import app
from api.tasks import ROUTE


client = TestClient(app)


def test_tasks_put():
    pass


def test_tasks_get():
    pass
