from flask import Flask
import os
import glob
from capitains_nautilus.cts.resolver import NautilusCTSResolver
from .bp import main_blueprint

chemin_actuel = os.path.dirname(os.path.abspath(__file__))
templates = os.path.join(chemin_actuel, "templates")
statics = os.path.join(chemin_actuel, "static")


def create_app(resolver="corpora/*"):
    app = Flask(
        "corpus-builder",
        template_folder=templates,
        static_folder=statics
    )

    app.resolver = NautilusCTSResolver(
        resource=glob.glob(resolver)
    )

    app.register_blueprint(main_blueprint)
    return app
