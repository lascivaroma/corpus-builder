from flask import Blueprint, \
                  render_template, \
                  current_app, \
                  jsonify, \
                  request, \
                  Response
from MyCapytain.common.constants import Mimetypes
from lxml import etree
from .utils import make_path
import glob
import os
import re


SPACE_SPLIT = re.compile("((\w+)(\W*))")


main_blueprint = Blueprint(
    "main",
    import_name="main",
    url_prefix="",
    template_folder=make_path("templates"),
    static_folder=make_path("assets")
)


@main_blueprint.route("/")
def index():
    """ Main form

    """
    return render_template("index.html")


@main_blueprint.route("/api/save", methods=["GET", "POST"])
def save():
    xml = request.form.get("xml")

    os.makedirs(current_app.save_folder, exist_ok=True)

    files = glob.glob(os.path.join(current_app.save_folder, "*.xml"))

    output_file = os.path.join(
        current_app.save_folder,
        "{}.xml".format(len(files))
    )
    with open(output_file, "w") as f:
        f.write(xml)

    return jsonify({"status": "ok", "path": os.path.abspath(output_file)})


@main_blueprint.route("/api/lemmatize", methods=["GET", "POST"])
def lemmatize():
    _in = request.form.get("plain-text")
    words = ""
    texts = list(SPACE_SPLIT.findall(_in))
    for index, lemmatisation in enumerate(current_app.lemmatizer.lemmatise_multiple(_in)):
        possible_lemma = set([proposal["lemma"] for proposal in lemmatisation])
        words += """\n        <w lemma="{lemma}">{form}</w>{after}""".format(
            form=texts[index][1],
            lemma="|".join(possible_lemma),
            after=texts[index][2]
        )

    template = """<div type="fragment" corresp="adams:{page}" ana="#{category}">
    <quote xml:lang="lat" source="{source}">{words}    
    </quote>
 </div>
""".format(
        page=request.form.get("pb", "page"),
        category=request.form.get("category", "category"),
        source=request.form.get("source-id"),
        words=words
    )
    return Response(
        template,
        headers={"Content-type": "application/xml"}
    )


@main_blueprint.route("/api/texts")
def authors():
    """ Retrieves authors for autocomplete

    :return: Dictionary with text key in JSON
    """
    return jsonify([
        {
            "id": collection.id,
            "title": collection.get_label(),
            "author": collection.parent.parent.get_label()
        }
        for collection in current_app.resolver.getMetadata().readableDescendants
        if collection
    ])


@main_blueprint.route("/api/passage")
def passage():
    """ Retrieves a passage

    :return: Dictionary with text key in JSON
    """
    objectId = request.args.get("id")
    passageId = request.args.get("passage")
    passage = current_app.resolver.getTextualNode(
        textId=objectId,
        subreference=passageId
    )
    xml = passage.export(Mimetypes.PYTHON.ETREE)

    with open(make_path("plaintext.xsl")) as f:
        xsl = etree.XSLT(etree.parse(f))

    xml = xsl(xml)

    return jsonify({"text": str(xml)})