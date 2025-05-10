import typer

app = typer.Typer()


@app.command(name="anon")
def anonymize():
    pass


@app.command(name="merge")
def merge():
    pass


@app.command(name="parse")
def parse():
    pass


@app.command(name="gen")
def gen():
    pass
