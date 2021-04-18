from flask_restful import Resource as _Resource

from db.tasks import get_all_tasks


class Tasks(_Resource):
    """
    retrieve all tasks definitions
    """
    route = "/tasks"

    def get(self):  # todo: add pagination
        return [task.json() for task in get_all_tasks()]
