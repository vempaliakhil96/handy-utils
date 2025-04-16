"""Console script for handy_utils."""
import click

from handy_utils.configuration import generate_config, get_config_path, view_config
from handy_utils.generate_commit import generate_llm_commit_message, perform_commit
from handy_utils.convert_to_confluence import convert_to_confluence

@click.group("handy-utils")
def main():
    """Handy Utils CLI."""
    pass


@click.command("generate-commit")
@click.option("--jira-ticket", type=str, help="Jira ticket number.")
@click.option("--dry-run", is_flag=True, help="Dry run the commit generation.")
def generate_commit_command(jira_ticket: str, dry_run: bool):
    """Generate a commit message for the changes."""
    commit_message = generate_llm_commit_message(jira_ticket)
    click.echo(commit_message)
    if dry_run:
        click.echo("Dry run completed.")
        return
    k = click.prompt("confirm commit message (y/n) or edit (e)", type=click.Choice(['y', 'n', 'e']))
    if k == 'y':
        perform_commit(commit_message)
    elif k == 'e':
        new_commit_message = click.edit(commit_message)
        perform_commit(new_commit_message)
    else:
        click.echo("Commit not generated.")


@click.command("nb2conf")
@click.argument("notebook_path", type=click.Path(exists=True))
@click.option("--output-path", type=click.Path(), help="Path to the output html file.", default=None)
@click.option("--dry-run", is_flag=True, help="Dry run the conversion.", default=False)
def convert_to_confluence_command(notebook_path: str, output_path: str, dry_run: bool):
    """
    Convert a notebook to Confluence. You can add the following tags at the start of each cell to control the conversion: \b

    - `#|nb_tag: skip` - skip the cell \n
    - `#|nb_tag: remove_output` - remove the output of the cell \n
    - `#|nb_tag: remove_input` - remove the input of the cell \n
    """
    convert_to_confluence(notebook_path, output_path, dry_run)

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
main.add_command(convert_to_confluence_command)
if __name__ == "__main__":
    main()  # pragma: no cover