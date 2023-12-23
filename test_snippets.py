import os
import sys
import io

from snippettesterlib import config, addAction, iterateSnippets, run, show
import pytest
from zoofc1 import ZoofCompiler, Source

# when I run this in my IDE, load these in the env
from zoofc1.tokens import TokenType as TT  # noqa


# %% Configure

config.rootDir = os.path.dirname(__file__)
config.dirs = ["snippets"]
config.separator = "####"
config.pattern = "*.zf"


@addAction("noop")
def action_noop(snippet):
    return ""


@addAction("repr")
def action_repr(snippet):
    # Really just for testing the snippet mechanics
    return repr(snippet.source)


@addAction("tokenize")
def action_tokenize(snippet):
    c = ZoofCompiler()
    m = c.createModule("main")
    s = Source("snippet", 1, snippet.source)
    lines = []
    for token in m.tokenize(s):
        lines.append(
            f"{token.typename} {token.lexeme!r} at {token.line}:{token.column}"
        )
    return "\n".join(lines)


@addAction("exec")
def action_exec(snippet):
    file = io.StringIO()
    c = ZoofCompiler(file)
    s = Source("snippet", 1, snippet.source)
    m = c.createModule("main")
    m.execute(s)
    return file.getvalue().rstrip()


@addAction("repl")
def action_repl(snippet):
    fname = os.path.relpath(snippet.filename, config.rootDir)
    m = MODULES.get(fname, None)
    if m is None:
        c = ZoofCompiler()
        m = c.createModule("main")
        MODULES[fname] = m

    m.compiler.stdout = stdout = io.StringIO()

    s = Source(fname, snippet.linenr + 1, snippet.source)
    m.execute(s)
    return stdout.getvalue().rstrip()


MODULES = {}


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
