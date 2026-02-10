from pathlib import Path
from datetime import datetime, timezone
import yaml
import typer
from docktapus.app import app

OCT_CONFIG = ".oct.yml"


@app.command()
def init(
    project_name: str = typer.Argument(..., help="Project name"),
    dev_compose_file: Path = typer.Option(
        ..., "--dev-compose-file", help="Pat to dev docker-compose file"
    ),
    prod_compose_file: Path = typer.Option(
        ..., "--prod-compose-file", help="Pat to prod docker-compose file"
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite existing .oct.yml"),
):
    cwd = Path.cwd()
    config_path = cwd / OCT_CONFIG

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
    typer.echo(f"Root:  {cwd.resolve()}")
    typer.echo(f"Dev:   {dev_path}")
    typer.echo(f"Prod:  {prod_path}")
