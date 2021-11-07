import click

from orchestrator.cli import orchestrator


@click.group()
def cli():
    pass


cli.add_command(orchestrator)


if __name__ == "__main__":
    cli()
