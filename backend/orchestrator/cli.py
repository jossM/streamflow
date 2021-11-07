import click
from orchestrator.main_orchestrator import start


@click.group()
def orchestrator():
    pass


orchestrator.add_command(start)
