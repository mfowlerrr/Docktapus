import json
import subprocess
from pathlib import Path

import typer


def _get_containers(project_name: str | None = None) -> list[dict]:
    """Return container details filtered by dtop labels."""
    filter_args = ["--filter", "label=dtop.project"]
    if project_name:
        filter_args = ["--filter", f"label=dtop.project={project_name}"]

    result = subprocess.run(
        [
            "docker",
            "ps",
            "-a",
            *filter_args,
            "--format",
            "{{json .}}",
        ],
        capture_output=True,
        text=True,
    )
    containers = []
    for line in result.stdout.strip().splitlines():
        if line:
            containers.append(json.loads(line))
    return containers


def _get_label(labels_str: str, key: str) -> str:
    """Extract a label value from the docker Labels string."""
    for part in labels_str.split(","):
        if part.strip().startswith(f"{key}="):
            return part.strip().split("=", 1)[1]
    return ""


def ls(
    project_name: str = typer.Argument(
        None, help="Project to list (defaults to all projects)"
    ),
):
    """
    List Docktapus-managed containers.

    Shows all projects and their containers with status, ports, image,
    and whether each container is running in dev or prod mode.

    Usage:
      dtop ls [PROJECT_NAME]

    Examples:
      dtop ls
      dtop ls myproj
    """
    containers = _get_containers(project_name)

    if not containers:
        if project_name:
            typer.echo(f"No containers found for project '{project_name}'")
        else:
            typer.echo("No Docktapus-managed containers found")
        raise typer.Exit()

    # Group by project
    projects: dict[str, list[dict]] = {}
    for c in containers:
        proj = _get_label(c.get("Labels", ""), "dtop.project")
        projects.setdefault(proj, []).append(c)

    # Column headers
    hdr = f"{'CONTAINER ID':<15} {'SERVICE':<20} {'CONTAINER NAME':<30} {'IMAGE':<30} {'STATUS':<20} {'PORTS':<30} {'ENV':<6}"
    sep = "-" * len(hdr)

    for proj_name in sorted(projects):
        typer.echo(f"\nProject: {proj_name}")
        typer.echo(sep)
        typer.echo(hdr)
        typer.echo(sep)
        for c in sorted(projects[proj_name], key=lambda x: x.get("Names", "")):
            env = _get_label(c.get("Labels", ""), "dtop.env")
            service = _get_label(c.get("Labels", ""), "com.docker.compose.service")
            typer.echo(
                f"{c.get('ID', ''):<15} "
                f"{service:<20} "
                f"{c.get('Names', ''):<30} "
                f"{c.get('Image', ''):<30} "
                f"{c.get('Status', ''):<20} "
                f"{c.get('Ports', ''):<30} "
                f"{env:<6}"
            )
        typer.echo("")
