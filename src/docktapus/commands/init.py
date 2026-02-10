from pathlib import Path
from datetime import datetime, timezone
import yaml
import typer

OCT_CONFIG = Path.home() / ".dtop.yml"


def init(
    project_name: str = typer.Argument(..., help="Project name"),
    dev_compose_file: Path = typer.Option(
        ..., "-dcf", "--dev-compose-file", help="Path to dev docker-compose file"
    ),
    prod_compose_file: Path = typer.Option(
        ..., "-pcf", "--prod-compose-file", help="Path to prod docker-compose file"
    ),
    config_path: Path = typer.Option(
        None, "-conf", "--config-file-path", help="Path to .dtop.yml config file"
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite existing .oct.yml"),
):
    """
    Initialize a Docktapus project.

    This registers a project with Docktapus by recording the locations of
    your production and development docker-compose files. No containers
    are started and no Docker commands are run.

    A single .oct.yml file can contain multiple projects.
    """

    if not config_path.is_file():
        typer.echo(f"Using default config path {OCT_CONFIG} ")
        config_path = OCT_CONFIG
    cwd = Path.cwd()

    dev_path = dev_compose_file.expanduser().resolve()
    prod_path = prod_compose_file.expanduser().resolve()

    # Raise errors if files don't exist
    if not dev_path.is_file():
        typer.echo(f"❌ Dev compose not found: {dev_path}")
        raise typer.Exit(code=1)

    if not prod_path.is_file():
        typer.echo(f"❌ Prod compose not found: {prod_path}")
        raise typer.Exit(code=1)

    # Load existing config or create a new one

    if config_path.exists():
        with config_path.open() as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}

    projects = config.setdefault("projects", {})

    if project_name in projects and not force:
        typer.echo(
            f"❌ Project {project_name} already exists! Use --force to overwrite"
        )
        raise typer.Exit(code=1)

    projects[project_name] = {
        "root": str(cwd.resolve()),
        "compose": {"dev": str(dev_path), "prod": str(prod_path)},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with config_path.open("w") as f:
        yaml.safe_dump(config, f, sort_keys=False)

    typer.echo("Project initialised")
    typer.echo(f"Project: {project_name}")
    typer.echo(f"Project Root:  {cwd.resolve()}")
    typer.echo(f"Dev:   {dev_path}")
    typer.echo(f"Prod:  {prod_path}")
