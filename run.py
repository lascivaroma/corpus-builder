from app import create_app
import click


@click.group()
def cli():
    pass


@click.command("clear")
@click.option("--cache", default="cache", help="Path to the cache the resolver")
def clear(cache="cache"):
    click.echo("Clearing cache")
    app, cache = create_app(cache=cache)
    cache.clear()


@click.command("run")
@click.option("--debug", is_flag=True, help="Run flask in debug mode")
@click.option("--data", default="data/*/*", help="Path to the corpora containing directory")
@click.option("--cache", default="cache", help="Path to the cache the resolver")
@click.option("--save", "save_folder", default="output", help="Path which will contain the results")
def run(debug=False, data="data", cache="cache", save_folder="output"):
    app, cache = create_app(resolver=data, cache=cache, save_folder=save_folder)
    app.debug = debug
    app.run()


cli.add_command(run)
cli.add_command(clear)


if __name__ == "__main__":
    cli()
