import typer
from docktapus.commands.init import init

app = typer.Typer(name="Docktapus")

app.command("init")(init)

if __name__ == "__main__":
    app()
