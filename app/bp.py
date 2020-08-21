from flask import Blueprint, \
                  render_template, \
                  current_app, \
                  jsonify, \
                  request, \
                  Response, \
                  send_file
from MyCapytain.common.constants import Mimetypes
from lxml import etree
from .utils import make_path, get_tags
import glob
import os
import re
import zipfile
import time
from io import BytesIO
import requests


SPACE_SPLIT = re.compile("((\w+)(\W*))")

with open(os.path.join(os.path.dirname(__file__), "assets", "include.xsl")) as f:
    XSL = etree.XSLT(etree.parse(f))

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
    return render_template("index.html", tags=get_tags())


@main_blueprint.route("/group")
def group():
    """ Main form

    """
    return render_template("group.html", tags=get_tags())


_keys = ("ref", "lemma", "pos", "msd",)


def build(hits, keys=_keys, ana="", remove_before_dot=False, remove_after_dot=False):
    refs, ref_type, data = [], [], []
    for token in zip(*hits.values()):
        token = dict(zip(hits.keys(), token))
        refs.append(token["ref"])
        ref_type.append(token["in"])
        data.append(
            "<w " + ana + " ".join(
                ["{}=\"{}\"".format(k, token[k]) for k in keys]
            ) + ">" + token["word"] + "</w>"
        )
        if token["lemma"] in {".", "?", "!"}:
            if remove_before_dot:
                refs, ref_type, data = [], [], []
            elif remove_after_dot:
                break
    return refs, ref_type, data


XML_SCHEME = """
<div type="fragment" corresp="adams:{page}" ana="{full_analysis}">
  <bibl><author>{author}</author>, <title>{title}</title>, <biblScope>{ref}</biblScope></bibl>
  <quote xml:lang="lat" source="{tid}:{ref}" type="{ref_type}">
    {words}
  </quote>
</div>
"""


@main_blueprint.route("/api/search")
def search():
    """

    Request params:
        - query
        - filter
        - page
        - analysis
        - full_analysis
        - text-filter

    """
    corpus = "lemmatized"
    server = "http://localhost:8888/blacklab-server/{}-index/hits".format(corpus)

    _filter = []
    text_filter = request.args.get("text-filter")
    if text_filter:
        text_filter = text_filter.replace('.', '\\.').replace('\\.*', '.*').replace("-", "\\-").replace(":", "\\:")
        _filter.append(f"docId:{text_filter}")

    category = ["#"+cat.strip("#") for cat in request.args.get("category", "").split()]
    full_analysis = request.args.getlist("tradicategory") + \
        request.args.getlist("sourced-tags") + category
    full_analysis = ["#"+cat.strip("#") for cat in full_analysis]

    req = requests.post(server, data={
        "patt": request.args.get("query"),
        "filter": ";".join(_filter) or None,
        "wordsaroundhit": 30,
        "usecontent": "fi",  # Slower but better for my purposes
        "outputformat": "json",
        "prettyprint": True
    })

    resp = req.json()
    if "hits" not in resp:
        return "<h3>Error</h3><pre>{}</pre>".format(str(resp))
    elif len(resp["hits"]) == 0:
        return "<em>No results</em>"
    out = """<results>"""

    for hit in resp["hits"]:
        data = []
        refs = []
        ref_type = []
        doc = hit["docPid"]
        title = resp["docInfos"][doc]["title"][0]
        author = resp["docInfos"][doc]["author"][0]
        r, t, d = build(hit["left"], remove_before_dot=True)
        refs.extend(r), ref_type.extend(t), data.extend(d)
        r, t, d = build(hit["match"], ana=f' ana="{" ".join(category)}" ')
        refs.extend(r), ref_type.extend(t), data.extend(d)
        r, t, d = build(hit["right"], remove_after_dot=True)
        refs.extend(r), ref_type.extend(t), data.extend(d)

        out += XML_SCHEME.format(
                words="\n    ".join(data).replace('"""', "'\"'"),
                tid=resp["docInfos"][doc]["docId"][0],
                ref="-".join([refs[0], refs[-1]]),
                ref_type=ref_type[0],
                page=request.args.get("page", ""),
                full_analysis=" ".join(full_analysis),
                author=author,
                title=title
            )

    return Response(
        str(XSL(etree.fromstring(out+"</results>"))),
        mimetype='text/html'
    )


@main_blueprint.route("/output")
def current_output():
    """ Render current output
    """
    done = ["<div>"]
    files = glob.glob(os.path.join(current_app.save_folder, "*.xml"))

    for file_id in range(len(files)):
        with open(os.path.join(current_app.save_folder, "{}.xml".format(file_id))) as f:
            done.append(f.read())

    return Response(
        "\n".join(
            done + ["</div>"]
        ),
        headers={"Content-type": "application/xml"}
    )


@main_blueprint.route("/download")
def download():
    """ Render current output
    """
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        files = glob.glob(os.path.join(current_app.save_folder, "*.xml"))
        for individualFile in files:
            filename = os.path.basename(individualFile)
            data = zipfile.ZipInfo(filename)
            data.date_time = time.localtime(time.time())[:6]
            data.compress_type = zipfile.ZIP_DEFLATED
            with open(individualFile) as f:
                zf.writestr(data, f.read())
    memory_file.seek(0)
    return send_file(memory_file, attachment_filename='corpus.zip', as_attachment=True)


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
        possible_lemma = [
            proposal["lemma"]+"("+proposal["morph"]+")"
            for proposal in lemmatisation
        ]
        words += """\n        <w lemma="{lemma}">{form}</w>{after}""".format(
            form=texts[index][1],
            lemma="|".join(possible_lemma),
            after=texts[index][2]
        )
    category = request.form.get("category", "")
    if category:
        category = "#" + category
    template = """<div type="fragment" corresp="adams:{page}" ana="{category} {addition_cats}">
    <quote xml:lang="lat" source="{source}">{words}    
    </quote>
 </div>
""".format(
        page=request.form.get("pb", "page"),
        category=category,
        source=request.form.get("source-id"),
        addition_cats=" ".join(request.form.getlist("tradicategory") + request.form.getlist("sourced-tags")),
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
        if collection and collection.lang == "lat"
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
    xml = passage.export(Mimetypes.PYTHON.ETREE)#

    with open(make_path("plaintext.xsl")) as f:
        xsl = etree.XSLT(etree.parse(f))

    xml = xsl(xml)

    return jsonify({"text": str(xml)})


@main_blueprint.route("/api/tags")
def tags():
    """ Retrieves a passage

    :return: Dictionary with text key in JSON
    """
    return jsonify(get_tags(clear_cache=True))


@main_blueprint.errorhandler(ReferenceError)
def handle_invalid_usage(error):
    return Response(
        "Unknown reference", status=404,
        headers={"Content-type": "text/plain"}
    )
