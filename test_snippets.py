import os
import sys
import io

from snippettesterlib import config, addAction, iterateSnippets, run, show
import pytest
from zoofc1 import ZoofCompiler


# %% Configure

config.rootDir = os.path.dirname(__file__)
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
    lines = []
    for token in c.tokenize(source):
        lines.append(
            f"{token.typename} {token.lexeme!r} at {token.line}:{token.column}"
        )
    return "\n".join(lines)


@addAction("exec")
def action_exec(source):
    file = io.StringIO()
    c = ZoofCompiler(file)
    c.run(source)
    return file.getvalue().rstrip()


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
