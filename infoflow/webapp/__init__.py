"""Packaged, build-free web assets."""
from importlib.resources import files


def asset(name):
    return files(__package__).joinpath(name).read_bytes()


INDEX_HTML = asset("index.html").decode("utf-8")
