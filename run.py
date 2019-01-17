from app import create_app
import click
import re
import lxml.etree as etree
import MyCapytain.common.constants as c


class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'


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


@cli.command("search")
@click.argument("text_id", "text")
@click.option("--w1", help="Search")
@click.option("--w2", help="Search", multiple=True)
@click.option("--depth", help="Search", type=int)
@click.option("--data", default="data/*/*", help="Path to the corpora containing directory")
@click.option("--data", default="data/*/*", help="Path to the corpora containing directory")
@click.option("--xsl", default="app/plaintext.xsl", help="XSL")
def search(text_id, w1=None, w2=None, data="data/*/*", depth=1, xsl=None):
    """ """
    app, cache = create_app(resolver=data, cache="cache")
    resolver = app.resolver
    w2 = "|".join([
        "({})".format(w)
        for w in w2
    ])
    with open(xsl) as xsl_file:
        transform = etree.XSLT(etree.parse(xsl_file))

    texts = [
        (ref, str(transform(resolver.getTextualNode(textId=text_id, subreference=ref).export(
            c.Mimetypes.PYTHON.ETREE))))
        for ref in resolver.getReffs(textId=text_id, level=depth)
    ]

    r1 = " ((?P<w1>"+w1+")\s+(?P<wm>(\w+\s+){1,2})?(?P<w2>"+w2+"))"
    r2 = " ((?P<w1>"+w2+")\s+(?P<wm>(\w+\s+){1,2})?(?P<w2>"+w1+"))"
    s = re.compile(r"\s+")
    normalizer = lambda x: s.sub(" ", x)
    repl = color.RED + " \\g<w1>" + color.END + " \\g<wm>" + color.RED + "\\g<w2>" + color.END
    sub = lambda s, reg: re.sub(reg, repl, normalizer(s), re.MULTILINE)
    cnt = 0
    for ref, plain_text in texts:
        for sentence in plain_text.split("."):
            sentence = " " + sentence
            if re.findall(r1, sentence) or re.findall(r2, sentence):
                print(text_id+":"+ref+"\t"+sub(sub(sentence, r1), r2) + ".")
                cnt += 1

    print("{} results".format(cnt))


cli.add_command(run)
cli.add_command(clear)


if __name__ == "__main__":
    cli()
