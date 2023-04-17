import os
import sys

import pytest

from snippettesterlib import config, addAction, iterateSnippets, run, show


# %% Configure

config.dirs = ["snippets"]
config.separator = "####"
config.pattern = "*.zf"


@addAction("repr")
def action_repr(source):
    return repr(source)


@addAction("tokenize")
def action_tokenize(source):
    return "TODO"


@addAction("exec")
def action_exec(source):
    return "TODO"


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
