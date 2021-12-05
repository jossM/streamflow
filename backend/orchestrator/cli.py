import click
from orchestrator.main_orchestrator import start
from orchestrator.main_task_handler import start_task


@click.group()
def orchestrator():
    pass


orchestrator.add_command(start)
orchestrator.add_command(start_task)