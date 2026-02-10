# 🐙 Docktapus

Manage dev and prod Docker Compose environments side by side. Docktapus lets you register projects with separate dev and prod compose files, then selectively bring up services and swap between environments with a single command.

## Requirements

- Python 3.12+
- Docker with the Compose V2 plugin (`docker compose`)

## Install

```bash
pip install git+https://github.com/mfowlerrr/docktapus.git
```

Or clone and install locally:

```bash
git clone https://github.com/mfowlerrr/docktapus.git
cd docktapus
pip install .
```

This makes both `docktapus` and the shorthand `dtop` available on your PATH.

## Usage

```
dtop init       Register a new project with its dev & prod compose files
dtop update     Update an existing project's configuration
dtop up         Start containers (dev services + non-colliding prod services)
dtop down       Stop and remove containers for a project
dtop ls         List all Docktapus-managed containers
dtop swap       Swap a service between dev and prod environments
```

Run `dtop <command> --help` for details on a specific command.