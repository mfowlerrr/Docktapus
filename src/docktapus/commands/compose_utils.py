import copy
import subprocess

import typer


def _network_exists(name: str) -> bool:
    result = subprocess.run(
        ["docker", "network", "inspect", name],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def _volume_exists(name: str) -> bool:
    result = subprocess.run(
        ["docker", "volume", "inspect", name],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def ensure_networks(compose_data: dict, project_name: str) -> dict:
    """Pre-create networks or join existing ones, rewriting compose to use external networks.

    For every top-level network in the compose data, check if it already
    exists.  If it does, join it as-is.  If not, create it with a
    dtop.project label so it can be cleaned up later.  Either way the
    compose entry is marked external so both prod and dev runs share
    the same Docker network.
    """
    data = copy.deepcopy(compose_data)
    networks = data.get("networks")
    if not networks:
        return data

    for net_name, net_cfg in networks.items():
        if isinstance(net_cfg, dict) and net_cfg.get("name"):
            docker_name = net_cfg["name"]
        else:
            docker_name = net_name

        if _network_exists(docker_name):
            typer.echo(f"  ↳ network '{docker_name}' already exists, joining")
        else:
            typer.echo(f"  ↳ creating network '{docker_name}'")
            cmd = [
                "docker", "network", "create",
                "--driver", "bridge",
                "--label", f"dtop.project={project_name}",
                docker_name,
            ]
            subprocess.run(cmd, check=True, capture_output=True)

        data["networks"][net_name] = {"name": docker_name, "external": True}

    return data


def ensure_volumes(compose_data: dict, project_name: str) -> dict:
    """Pre-create volumes or join existing ones, rewriting compose to use external volumes.

    Same pattern as ensure_networks but for Docker volumes.
    """
    data = copy.deepcopy(compose_data)
    volumes = data.get("volumes")
    if not volumes:
        return data

    for vol_name, vol_cfg in volumes.items():
        if isinstance(vol_cfg, dict) and vol_cfg.get("name"):
            docker_name = vol_cfg["name"]
        else:
            docker_name = vol_name

        if _volume_exists(docker_name):
            typer.echo(f"  ↳ volume '{docker_name}' already exists, joining")
        else:
            typer.echo(f"  ↳ creating volume '{docker_name}'")
            cmd = [
                "docker", "volume", "create",
                "--label", f"dtop.project={project_name}",
                docker_name,
            ]
            subprocess.run(cmd, check=True, capture_output=True)

        data["volumes"][vol_name] = {"name": docker_name, "external": True}

    return data


def prepare_compose(compose_data: dict, project_name: str) -> dict:
    """Ensure shared networks and volumes exist, returning a modified compose dict."""
    data = ensure_networks(compose_data, project_name)
    data = ensure_volumes(data, project_name)
    return data


def cleanup_networks(project_name: str):
    """Remove Docker networks labelled with dtop.project=<project_name>."""
    result = subprocess.run(
        [
            "docker", "network", "ls",
            "--filter", f"label=dtop.project={project_name}",
            "--format", "{{.ID}}",
        ],
        capture_output=True, text=True,
    )
    network_ids = [nid for nid in result.stdout.strip().splitlines() if nid]
    for nid in network_ids:
        subprocess.run(["docker", "network", "rm", nid], capture_output=True)


def cleanup_volumes(project_name: str):
    """Remove Docker volumes labelled with dtop.project=<project_name>."""
    result = subprocess.run(
        [
            "docker", "volume", "ls",
            "--filter", f"label=dtop.project={project_name}",
            "--format", "{{.Name}}",
        ],
        capture_output=True, text=True,
    )
    volume_names = [v for v in result.stdout.strip().splitlines() if v]
    for v in volume_names:
        subprocess.run(["docker", "volume", "rm", v], capture_output=True)
