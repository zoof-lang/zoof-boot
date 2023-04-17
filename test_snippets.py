import os
import sys
import io

from snippettesterlib import config, addAction, iterateSnippets, run, show
import pytest
from zoofc1 import ZoofCompiler


# %% Configure

config.dirs = ["snippets"]
config.separator = "####"
config.pattern = "*.zf"


@addAction("repr")
def action_repr(source):
    # Really just for testing the snippet mechanics
    return repr(source)


@addAction("tokenize")
def action_tokenize(source):
    c = ZoofCompiler()
    return "\n".join(repr(t) for t in c.tokenize(source))


@addAction("exec")
def action_exec(source):
    file = io.StringIO()
    c = ZoofCompiler(file)
    c.run(source)
    return file.getvalue().rstrip()


@addAction("eval")
def action_eval(source):
    return "TODO"


# %% Can run this file with pytest


@pytest.mark.parametrize("name,snippet", [(s.repr(), s) for s in iterateSnippets()])
def test_snippet(name, snippet):
    snippet.run()
    assert snippet.result == snippet.expect


# %% Can run this file directly (also in an IDE)

if __name__ == "__main__":
    if sys.argv[-1] == "show":
        show()
    else:
        if not run():
            raise RuntimeError("Snippet test failed")
