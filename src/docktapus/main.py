from docktapus.commands.init import init
from docktapus.commands.update import update
from docktapus.commands.up import up
from docktapus.commands.down import down
import typer

app = typer.Typer(
    name="Docktapus",
    help="Docktapus CLI - manage dev and prod Docker Compose environments",
)

app.command("init")(init)
app.command("update")(update)
app.command("up")(up)
app.command("down")(down)

if __name__ == "__main__":
    app()
