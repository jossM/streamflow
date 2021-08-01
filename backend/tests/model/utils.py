from model.task_model import Task


def make_task(id='id/task', **kwargs) -> Task:
    if not kwargs:
        kwargs["pod_template"] = "template"
    return Task.construct(
        id=id,
        **kwargs
    )


def make_task_dict(**kwargs) -> dict:
    return make_task(**kwargs).dict()

