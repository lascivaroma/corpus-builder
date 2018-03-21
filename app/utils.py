import os

chemin_actuel = os.path.dirname(os.path.abspath(__file__))


def make_path(*args):
    return os.path.join(chemin_actuel, *args)
