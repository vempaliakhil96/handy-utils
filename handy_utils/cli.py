"""Console script for handy_utils."""
from handy_utils.generate_commit import generate_commit
from handy_utils.configuration import generate_config, view_config, get_config_path
import click


@click.group()
def main():
    pass

@click.command("generate-commit")
@click.option("--dry-run", is_flag=True, help="Dry run the commit generation.")
def generate_commit_command(dry_run):
    generate_commit(dry_run)


@click.group("config")
def config_group():
    pass

@click.command("generate")
def generate_config_command():
    generate_config()

@click.command("view")
def view_config_command():
    click.echo(view_config())

@click.command("path")
def view_config_path_command():
    click.echo(get_config_path())

main.add_command(generate_commit_command)
config_group.add_command(generate_config_command)
config_group.add_command(view_config_command)
config_group.add_command(view_config_path_command)
main.add_command(config_group)

if __name__ == "__main__":
    main()  # pragma: no cover
