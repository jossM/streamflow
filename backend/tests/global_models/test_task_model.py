from pydantic import ValidationError
from pytest import raises

from db.db_model import DbTask
from tests.global_models.utils import make_task_dict


def test_db_task_validation_can_pass():
    task_data = make_task_dict()
    DbTask(**task_data)


def test_task_must_contain_one_template():
    task_data = make_task_dict()
    task_data.pop("call_template", None)
    with raises(ValidationError):
        DbTask(**task_data)


def test_task_id_must_contain_dag():
    task_data = make_task_dict(id="no_separator_indicating_dage_of_task")
    with raises(ValidationError):
        DbTask(**task_data)
