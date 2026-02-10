from pathlib import Path
from datetime import datetime, timezone
import yaml
import typer

OCT_CONFIG = Path.home() / ".dtop.yml"


def update(
    project_name: str = typer.Argument(
        None, help="Name of the project to update (defaults to current folder name)"
    ),
    root: Path = typer.Option(None, "--root", help="Update the project root directory"),
    dev_compose_file: Path = typer.Option(
        None,
        "-dcf",
        "--dev-compose-file",
        help="Update the path to the dev docker-compose file",
    ),
    prod_compose_file: Path = typer.Option(
        None,
        "-pcf",
        "--prod-compose-file",
        help="Update the path to the prod docker-compose file",
    ),
    config_path: Path = typer.Option(
        None, "-conf", "--config-file-path", help="Path to .dtop.yml config file"
    ),
    force: bool = typer.Option(
        False, "--force", help="Overwrite existing values without confirmation"
    ),
):
    """
    Update an existing Docktapus project.

    Usage:
      dtop update [PROJECT_NAME] [OPTIONS]

    Only the fields you provide will be updated; all other settings
    remain unchanged. PROJECT_NAME defaults to the current folder
    name if not specified.

    Examples:
      dtop update myproj -dcf docker-compose.dev.yml
      dtop update myproj --root /new/project/path --force
    """
    if not project_name:
        project_name = Path.cwd().name

    if not config_path.is_file():
        typer.echo(f"Using default config path {OCT_CONFIG} ")
        config_path = OCT_CONFIG

    # Load config
    if not config_path.exists():
        typer.echo(f"❌ Config file not found: {config_path}")
        raise typer.Exit(code=1)

    with config_path.open() as f:
        config = yaml.safe_load(f) or {}

    projects = config.get("projects", {})
    if project_name not in projects:
        typer.echo(f"❌ Project '{project_name}' not found in {config_path}")
        raise typer.Exit(code=1)

    project = projects[project_name]

    # Update root if provided
    if root:
        root_path = root.expanduser().resolve()
        project["root"] = str(root_path)
        typer.echo(f"Updated project root: {root_path}")

    # Update dev compose file if provided
    if dev_compose_file:
        dev_path = dev_compose_file.expanduser().resolve()
        if not dev_path.is_file():
            typer.echo(f"❌ Dev compose file not found: {dev_path}")
            raise typer.Exit(code=1)
        project.setdefault("compose", {})["dev"] = str(dev_path)
        typer.echo(f"Updated dev compose: {dev_path}")

    # Update prod compose file if provided
    if prod_compose_file:
        prod_path = prod_compose_file.expanduser().resolve()
        if not prod_path.is_file():
            typer.echo(f"❌ Prod compose file not found: {prod_path}")
            raise typer.Exit(code=1)
        project.setdefault("compose", {})["prod"] = str(prod_path)
        typer.echo(f"Updated prod compose: {prod_path}")

    # Save updated config
    with config_path.open("w") as f:
        yaml.safe_dump(config, f, sort_keys=False)

    typer.echo(f"Project '{project_name}' updated successfully!")
