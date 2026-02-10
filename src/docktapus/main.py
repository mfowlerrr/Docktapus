from docktapus.commands.init import init
from docktapus.commands.update import update
from docktapus.commands.up import up
from docktapus.commands.down import down
from docktapus.commands.ls import ls
from docktapus.commands.swap import swap
import typer

app = typer.Typer(
    name="Docktapus",
    invoke_without_command=True,
    no_args_is_help=False,
)


@app.callback()
def main(ctx: typer.Context):
    """Docktapus CLI - manage dev and prod Docker Compose environments."""
    if ctx.invoked_subcommand is None:
        typer.echo(
            "🐙 Docktapus — manage dev & prod Docker Compose environments\n"
            "\n"
            "Usage: dtop <command> [options]\n"
            "\n"
            "Commands:\n"
            "  init     Register a new project with its dev & prod compose files\n"
            "  update   Update an existing project's configuration\n"
            "  up       Start containers (dev services + non-colliding prod services)\n"
            "  down     Stop and remove containers for a project\n"
            "  ls       List all Docktapus-managed containers\n"
            "  swap     Swap a service between dev and prod environments\n"
            "\n"
            "Run 'dtop <command> --help' for details on a specific command."
        )
        raise typer.Exit()


app.command("init")(init)
app.command("update")(update)
app.command("up")(up)
app.command("down")(down)
app.command("ls")(ls)
app.command("ps", hidden=True)(ls)
app.command("swap")(swap)

if __name__ == "__main__":
    app()
