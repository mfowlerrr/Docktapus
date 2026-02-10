from pathlib import Path
import copy
import os
import subprocess
import tempfile

import yaml
import typer

OCT_CONFIG = Path.home() / ".dtop.yml"


def _inject_labels(compose_data: dict, env: str, project_name: str) -> dict:
    """Return a copy of compose_data with dtop labels added to every service."""
    data = copy.deepcopy(compose_data)
    for svc_cfg in data.get("services", {}).values():
        labels = svc_cfg.get("labels", {})
        # Normalise list-style labels to dict
        if isinstance(labels, list):
            labels = dict(label.split("=", 1) for label in labels)
        labels["dtop.env"] = env
        labels["dtop.project"] = project_name
        svc_cfg["labels"] = labels
    return data


def _compose_up(compose_data: dict, services: list[str], build: bool):
    """Write compose_data to a temp file and run docker compose up on services."""
    fd, tmp = tempfile.mkstemp(suffix=".yml")
    try:
        with os.fdopen(fd, "w") as f:
            yaml.safe_dump(compose_data, f, sort_keys=False)
        cmd = ["docker", "compose", "-f", tmp, "up", "-d"]
        if build:
            cmd.insert(-1, "--build")
        if services:
            cmd.extend(services)
        typer.echo(f"  → {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    finally:
        os.unlink(tmp)


def up(
    project_name: str = typer.Argument(
        None, help="Project to run (defaults to current folder name)"
    ),
    dev: str = typer.Option(
        None,
        "--dev",
        help="Comma-separated list of dev services to run, or ALL for all dev services",
    ),
    config_path: Path = typer.Option(
        None, "-conf", "--config-file-path", help="Path to .dtop.yml config file"
    ),
    build: bool = typer.Option(
        False, "--build", help="Rebuild containers before starting"
    ),
):
    """
    Start Docker containers for a Docktapus project.

    Starts the requested dev services from the dev compose file and all
    prod services whose names do NOT collide with a requested dev service.
    Every container is labelled with dtop.env (prod/dev) and
    dtop.project (<project_name>).

    Usage:
      dtop up [PROJECT_NAME] [OPTIONS]

    Examples:
      dtop up myproj --build
      dtop up myproj --dev api,worker
      dtop up myproj --dev ALL
    """
    if not project_name:
        project_name = Path.cwd().name

    if not config_path or not config_path.is_file():
        typer.echo(f"Using default config path {OCT_CONFIG}")
        config_path = OCT_CONFIG

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
    dev_compose_path = project["compose"]["dev"]
    prod_compose_path = project["compose"]["prod"]

    # Load both compose files
    with open(dev_compose_path) as f:
        dev_compose = yaml.safe_load(f) or {}
    with open(prod_compose_path) as f:
        prod_compose = yaml.safe_load(f) or {}

    all_dev_service_names = list((dev_compose.get("services") or {}).keys())
    all_prod_service_names = list((prod_compose.get("services") or {}).keys())

    # Determine which dev services to start
    if dev:
        if dev.strip().upper() == "ALL":
            dev_to_start = all_dev_service_names
        else:
            dev_to_start = [s.strip() for s in dev.split(",") if s.strip()]
    else:
        dev_to_start = []

    # Prod services: everything NOT shadowed by a requested dev service
    prod_to_start = [s for s in all_prod_service_names if s not in dev_to_start]

    typer.echo(f"Project: {project_name}")
    if dev_to_start:
        typer.echo(f"Dev services:  {', '.join(dev_to_start)}")
    if prod_to_start:
        typer.echo(f"Prod services: {', '.join(prod_to_start)}")

    # Start prod services (labelled prod)
    if prod_to_start:
        prod_labelled = _inject_labels(prod_compose, "prod", project_name)
        _compose_up(prod_labelled, prod_to_start, build)

    # Start dev services (labelled dev)
    if dev_to_start:
        dev_labelled = _inject_labels(dev_compose, "dev", project_name)
        _compose_up(dev_labelled, dev_to_start, build)

    typer.echo("Services started")
