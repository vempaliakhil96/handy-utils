"""Console script for handy_utils."""
import click

from handy_utils.configuration import generate_config, get_config_path, view_config
from handy_utils.generate_commit import generate_llm_commit_message, perform_commit


@click.group()
def main():
    """Handy Utils CLI."""
    pass


@click.command("generate-commit")
@click.option("--dry-run", is_flag=True, help="Dry run the commit generation.")
def generate_commit_command(dry_run):
    """Generate a commit message for the changes."""
    commit_message = generate_llm_commit_message()
    click.echo(commit_message)
    k = click.prompt("confirm commit message (y/n) or edit (e)", type=click.Choice(['y', 'n', 'e']))
    if k == 'y':
        perform_commit(commit_message)
    elif k == 'e':
        new_commit_message = click.edit(commit_message)
        perform_commit(new_commit_message)
    else:
        click.echo("Commit not generated.")


@click.group("config")
def config_group():
    """Configuration commands."""
    pass


@click.command("generate")
def generate_config_command():
    """Generate a configuration file."""
    generate_config()


@click.command("view")
def view_config_command():
    """View the configuration."""
    click.echo(view_config())


@click.command("path")
def view_config_path_command():
    """View the path to the configuration file."""
    click.echo(get_config_path())


main.add_command(generate_commit_command)
config_group.add_command(generate_config_command)
config_group.add_command(view_config_command)
config_group.add_command(view_config_path_command)
main.add_command(config_group)

if __name__ == "__main__":
    main()  # pragma: no cover
