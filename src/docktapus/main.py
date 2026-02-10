from docktapus.commands.hello import hello
from docktapus.commands.init import init
from docktapus.commands.update import update
import typer

app = typer.Typer(
    name="Docktapus",
    help="Docktapus CLI - manage dev and prod Docker Compose environments",
)

app.command("hello")(hello)
app.command("init")(init)
app.command("update")(update)

if __name__ == "__main__":
    app()
