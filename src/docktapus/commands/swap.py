import json
import os
import subprocess
import tempfile
from pathlib import Path

import yaml
import typer

from docktapus.commands.up import OCT_CONFIG, _inject_labels, _compose_up


def _get_label(labels_str: str, key: str) -> str:
    """Extract a label value from the docker Labels string."""
    for part in labels_str.split(","):
        if part.strip().startswith(f"{key}="):
            return part.strip().split("=", 1)[1]
    return ""


def _get_service_env(project_name: str, service_name: str) -> str | None:
    """Return the dtop.env label ('prod' or 'dev') for a running service, or None."""
    result = subprocess.run(
        [
            "docker",
            "ps",
            "--filter", f"label=dtop.project={project_name}",
            "--format", "{{json .}}",
        ],
        capture_output=True,
        text=True,
    )
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        container = json.loads(line)
        labels = container.get("Labels", "")
        if _get_label(labels, "com.docker.compose.service") == service_name:
            env = _get_label(labels, "dtop.env")
            if env:
                return env
    return None


def _stop_service_containers(project_name: str, service_name: str):
    """Stop and remove containers for a specific service in a project."""
    result = subprocess.run(
        [
            "docker",
            "ps",
            "-a",
            "--filter", f"label=dtop.project={project_name}",
            "--format", "{{json .}}",
        ],
        capture_output=True,
        text=True,
    )
    container_ids = []
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        container = json.loads(line)
        labels = container.get("Labels", "")
        if _get_label(labels, "com.docker.compose.service") == service_name:
            container_ids.append(container.get("ID"))

    if container_ids:
        subprocess.run(["docker", "stop", *container_ids], check=True)
        subprocess.run(["docker", "rm", *container_ids], check=True)


def swap(
    project_name: str = typer.Argument(
        None, help="Project name (defaults to current folder name)"
    ),
    service_name: str = typer.Argument(
        ..., help="Service to swap between prod and dev"
    ),
    config_path: Path = typer.Option(
        None, "-conf", "--config-file-path", help="Path to .dtop.yml config file"
    ),
    build: bool = typer.Option(
        False, "--build", help="Rebuild containers before starting"
    ),
):
    """
    Swap a service between prod and dev.

    Detects whether the service is currently running as prod or dev,
    stops it, and starts the opposite version.

    Usage:
      dtop swap [PROJECT_NAME] SERVICE_NAME [OPTIONS]

    Examples:
      dtop swap myproj api
      dtop swap myproj api --build
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

    with open(dev_compose_path) as f:
        dev_compose = yaml.safe_load(f) or {}
    with open(prod_compose_path) as f:
        prod_compose = yaml.safe_load(f) or {}

    all_dev_services = list((dev_compose.get("services") or {}).keys())
    all_prod_services = list((prod_compose.get("services") or {}).keys())

    if service_name not in all_dev_services and service_name not in all_prod_services:
        typer.echo(f"❌ Service '{service_name}' not found in dev or prod compose files")
        raise typer.Exit(code=1)

    current_env = _get_service_env(project_name, service_name)

    if current_env is None:
        typer.echo(f"❌ Service '{service_name}' is not currently running in project '{project_name}'")
        raise typer.Exit(code=1)

    if current_env == "prod":
        target_env = "dev"
        if service_name not in all_dev_services:
            typer.echo(f"❌ Service '{service_name}' has no dev definition to swap to")
            raise typer.Exit(code=1)
        target_compose = dev_compose
    else:
        target_env = "prod"
        if service_name not in all_prod_services:
            typer.echo(f"❌ Service '{service_name}' has no prod definition to swap to")
            raise typer.Exit(code=1)
        target_compose = prod_compose

    typer.echo(f"Swapping '{service_name}' from {current_env} → {target_env}")

    # Stop the currently running service
    typer.echo(f"  Stopping {current_env} '{service_name}'...")
    _stop_service_containers(project_name, service_name)

    # Start the target version – build a minimal compose dict containing
    # only the service being swapped so Docker Compose doesn't touch others.
    typer.echo(f"  Starting {target_env} '{service_name}'...")
    minimal_compose = {
        k: v for k, v in target_compose.items() if k != "services"
    }
    minimal_compose["services"] = {
        service_name: target_compose["services"][service_name]
    }
    labelled = _inject_labels(minimal_compose, target_env, project_name)
    _compose_up(labelled, [service_name], build)

    typer.echo(f"✅ '{service_name}' is now running as {target_env}")
