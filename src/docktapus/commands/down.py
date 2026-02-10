import json
import subprocess

import typer

from docktapus.commands.compose_utils import cleanup_networks, cleanup_volumes


def _get_containers_by_project(project_name: str) -> list[str]:
    """Return container IDs labelled with dtop.project=<project_name>."""
    result = subprocess.run(
        [
            "docker",
            "ps",
            "-a",
            "--filter",
            f"label=dtop.project={project_name}",
            "--format",
            "{{.ID}}",
        ],
        capture_output=True,
        text=True,
    )
    return [cid for cid in result.stdout.strip().splitlines() if cid]


def down(
    project_name: str = typer.Argument(
        None, help="Project to stop (defaults to current folder name)"
    ),
):
    """
    Stop and remove Docker containers for a Docktapus project.

    Finds all running containers labelled with dtop.project=<project_name>
    and stops/removes them along with their networks.

    Usage:
      dtop down [PROJECT_NAME]

    Examples:
      dtop down myproj
      dtop down
    """
    from pathlib import Path

    if not project_name:
        project_name = Path.cwd().name

    container_ids = _get_containers_by_project(project_name)

    if not container_ids:
        typer.echo(f"No running containers found for project '{project_name}'")
        raise typer.Exit()

    typer.echo(f"Stopping {len(container_ids)} container(s) for project '{project_name}'...")

    # Stop containers
    subprocess.run(["docker", "stop", *container_ids], check=True)

    # Remove containers
    subprocess.run(["docker", "rm", *container_ids], check=True)

    # Clean up dtop-managed networks and volumes
    cleanup_networks(project_name)
    cleanup_volumes(project_name)

    typer.echo("Containers, networks, and volumes removed")
