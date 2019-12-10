import os
import json
import glob
from lxml import etree

chemin_actuel = os.path.dirname(os.path.abspath(__file__))


def make_path(*args):
    return os.path.join(chemin_actuel, *args)


def get_tags(clear_cache=False):
    cache_file = make_path("tags.json")
    if os.path.isfile(cache_file):
        if clear_cache:
            os.remove(cache_file)
        else:
            with open(cache_file) as f:
                return json.load(f)

    anas = []
    for file in glob.glob(make_path("../output/*.xml")):
        with open(file) as xml_file:
            xml = etree.parse(xml_file)
            for ana in xml.xpath("//@ana"):
                anas.extend([x.lstrip("#") for x in ana.split()])

    tags = sorted(list(set(anas)))
    with open(cache_file, "w") as f:
        json.dump(tags, f)
    return tags
