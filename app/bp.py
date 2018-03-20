from flask import Blueprint, \
                  render_template, \
                  current_app, \
                  jsonify, \
                  request
from MyCapytain.common.constants import Mimetypes
from lxml import etree


main_blueprint = Blueprint("main", import_name="main", url_prefix="")


@main_blueprint.route("/")
def index():
    return render_template("main.html")


@main_blueprint.route("/api/texts")
def authors():
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
    objectId = request.args.get("id")
    passage = request.args.get("passage")
    passage = current_app.resolver.getTextualNode(
        textId=objectId,
        subreference=passage
    )
    xml = passage.export(Mimetypes.PYTHON.ETREE)
    xsl = etree.XSL()
    # Continue in the future
