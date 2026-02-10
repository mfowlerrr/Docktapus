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
    remove_networks: bool = typer.Option(
        False,
        "--remove-networks",
        "-rn",
        help="Remove project networks without prompting",
    ),
    remove_volumes: bool = typer.Option(
        False,
        "--remove-volumes",
        "-rv",
        help="Remove project volumes without prompting",
    ),
    all_: bool = typer.Option(
        False,
        "--all",
        help="Remove everything (networks and volumes) without prompting",
    ),
):
    """
    Stop and remove Docker containers for a Docktapus project.

    Finds all running containers labelled with dtop.project=<project_name>
    and stops/removes them. By default you will be prompted whether to also
    remove networks and volumes.  Use --remove-networks, --remove-volumes,
    or --all to skip the prompts.

    Usage:
      dtop down [PROJECT_NAME] [OPTIONS]

    Examples:
      dtop down myproj
      dtop down myproj --all
      dtop down myproj --remove-networks
      dtop down
    """
    from pathlib import Path

    if not project_name:
        project_name = Path.cwd().name

    container_ids = _get_containers_by_project(project_name)

    if not container_ids:
        typer.echo(f"No running containers found for project '{project_name}'")
        raise typer.Exit()

    typer.echo(
        f"Stopping {len(container_ids)} container(s) for project '{project_name}'..."
    )

    # Stop containers
    subprocess.run(["docker", "stop", *container_ids], check=True)

    # Remove containers
    subprocess.run(["docker", "rm", *container_ids], check=True)

    removed = ["Containers"]

    # Determine whether to remove networks
    should_remove_networks = all_ or remove_networks
    if not should_remove_networks:
        should_remove_networks = typer.confirm(
            "Remove project networks?", default=False
        )

    if should_remove_networks:
        cleanup_networks(project_name)
        removed.append("networks")

    # Determine whether to remove volumes
    should_remove_volumes = all_ or remove_volumes
    if not should_remove_volumes:
        should_remove_volumes = typer.confirm("Remove project volumes?", default=False)

    if should_remove_volumes:
        cleanup_volumes(project_name)
        removed.append("volumes")

    typer.echo(f"{', '.join(removed)} removed")
