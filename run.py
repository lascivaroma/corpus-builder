from app import create_app
import click


@click.group()
def cli():
    pass


@click.command("run")
@click.option("--debug", is_flag=True, help="Run flask in debug mode")
@click.option("--resolver", default="data/*", help="Path to the corpora containing directory")
def run(debug=False, resolver="data"):
    app = create_app(resolver)
    app.resolver.parse()
    app.debug = debug
    app.run()

cli.add_command(run)

if __name__ == "__main__":
    cli()