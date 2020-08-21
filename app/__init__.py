from flask import Flask
import os
import glob
from MyCapytain.resolvers.cts.local import CtsCapitainsLocalResolver
from .bp import main_blueprint
from .utils import make_path
from pycollatinus import Lemmatiseur
import pickle


templates = make_path("templates")
statics = make_path("assets")

default_resolver = os.path.join("data", "*")


def create_app(resolver=default_resolver, save_folder="output", cache=make_path("..", "cache")):
    app = Flask(
        "corpus-builder",
        template_folder=templates,
        static_folder=statics
    )
    app.save_folder = save_folder

    # Loads or compile the Collatinus Lemmatizer
    lemmatiseur_pickle = os.path.join(cache, "collatinus.pickle")
    if os.path.isfile(lemmatiseur_pickle):
        lemmatizer = Lemmatiseur.load(lemmatiseur_pickle)
    else:
        lemmatizer = Lemmatiseur()
        with open(lemmatiseur_pickle, "wb") as f:
            pickle.dump(lemmatizer, f)

    app.lemmatizer = lemmatizer

    app.resolver = CtsCapitainsLocalResolver(
        resource=glob.glob(resolver)
    )

    app.register_blueprint(main_blueprint)
    return app, None
