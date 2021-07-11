from model.task_model import Task


def make_task_dict(id='dag/task', **kwargs) -> dict:
    if not kwargs:
        kwargs["pod_template"] = "template"
    return Task.construct(
        id=id,
        **kwargs
    ).dict()
