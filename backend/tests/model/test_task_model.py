from pydantic import ValidationError
from pytest import raises

from model.task_model import CallTask
from model.db import DbTask
from tests.model.utils import make_task_dict


def test_db_task_validation_can_pass():
    task_data = make_task_dict()
    DbTask(**task_data)


def test_task_can_only_contain_one_template():
    task_data = make_task_dict(
        pod_template="template",
        call_templates=[CallTask(url_template="url", method="POST")]
    )
    with raises(ValidationError):
        DbTask(**task_data)


def test_task_must_contain_at_most_one_template():
    task_data = make_task_dict(call_templates="template", pod_template="template")
    with raises(ValidationError):
        DbTask(**task_data)


def test_task_id_must_contain_dag():
    task_data = make_task_dict(id="no_separator_indicating_dage_of_task")
    with raises(ValidationError):
        DbTask(**task_data)
