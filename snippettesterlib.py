"""
Utility to execute and verify snippets. The idea is to import the lib
in a script, set the config and add actions. Then create files with
snippets!

Example script:

```py

    from snippettesterlib import config, addAction, iterateSnippets, run, show

    config.rootDir = os.path.dirname(__file__)
    config.dirs = ["snippets"]
    config.separator = "####"
    config.pattern = "*.py"


    @addAction("echo")
    def action_echo(source):
        return source


    if __name__ == "__main__":
        ok = run()
        sys.exit(0 if ok else 1)

```

Example snippet file:

```py

    # example snippetfile

    #### echo: foo
    foo
    #### output
    foo
    #### end


    #### echo: bar
    foo
    bar
    #### output
    foo
    bar
    #### end

```

"""


import os
import glob


__version__ = "0.1.0"
version_info = tuple(int(i) for i in __version__.split("."))


# %% Utils


class Config:
    pass


config = Config()

# Fields must be set from user-code
config.rootDir = os.path.dirname(__file__)
config.dirs = []
config.separator = "THE_SEPARATOR"
config.pattern = ""

# name -> func to apply to a snippet source
ACTIONS = {}


# %% API


def iterateSnippets():
    """A generator producing Snippet objects."""
    return SnippetCollection().iterSnippets()


def addAction(name):
    """Decorator to apply to a function to mark it as an action."""

    def wrapper(func):
        ACTIONS[name] = func
        return func

    return wrapper


def show():
    """Show a summary of the detected snippets."""
    collection = SnippetCollection()
    nfiles = len(collection.files)
    nsnippets = sum(len(file.snippets) for file in collection.files)
    print(f"Found {nfiles} files with a total of {nsnippets} snippets.")
    for snippet in collection.iterSnippets():
        print("    " + snippet.repr())


def run():
    """Run all snippets. Returns True if all results were as expected."""
    collection = SnippetCollection()

    nfiles = len(collection.files)
    nsnippets = sum(len(file.snippets) for file in collection.files)
    print(f"Found {nfiles} files with a total of {nsnippets} snippets.\n")

    missing = []
    fails = []

    for snippet in collection.iterSnippets():
        ok = snippet.run()
        res = "ok  " if ok else "FAIL"
        print(f"    {res} {snippet.repr(False)}")
        if not ok:
            if snippet.expect is None:
                missing.append(snippet)
            else:
                fails.append(snippet)
    print()

    for file in collection.files:
        file.save()

    if missing:
        print(f"Missing expected output for {len(missing)}/{nsnippets} snippets:")
        for snippet in missing:
            print("    " + snippet.repr(True, clickableFilename=True))
        print()
    if fails:
        print(f"Failed {len(fails)}/{nsnippets} snippets:")
        for snippet in fails:
            print("    " + snippet.repr(True, clickableFilename=True))
        print()
    else:
        print("No failed snippets.")
        print()

    if missing or fails:
        return False
    else:
        print(f"All {nsnippets} snippets passed :)")
        print()
        return True


# %% Core classes


class SnippetCollection:
    """Represents a set of files with snippets."""

    def __init__(self):
        self.dirnames = [os.path.join(config.rootDir, p) for p in config.dirs]
        self.collect()

    def collect(self):
        self.files = []

        for dirname in self.dirnames:
            assert os.path.isdir(dirname)
            filenames = glob.glob(
                os.path.join(dirname, "**", config.pattern), recursive=True
            )
            for filename in filenames:
                snippetFile = SnippetFile(filename)
                self.files.append(snippetFile)

    def iterSnippets(self):
        for file in self.files:
            for snippet in file.snippets:
                yield snippet


class SnippetFile:
    """Represents a file with zero or more snippets."""

    def __init__(self, filename):
        self.filename = filename
        self.load()

    def load(self):
        self.snippets = []

        assert os.path.isfile(self.filename)
        with open(self.filename, "rb") as f:
            self.text = f.read().decode()
        lines = self.text.split("\n")

        pending_snippet = None
        lastsep = 0

        for lineid, line in enumerate(lines):
            if line.startswith(config.separator):
                if ":" in line:
                    action, _, title = line[len(config.separator) :].partition(":")
                    action = action.strip()
                    title = title.strip()
                    if action:
                        pending_snippet = Snippet(
                            self.filename, lineid + 1, action, title
                        )
                        pending_snippet.linenr = lineid + 1
                elif pending_snippet:
                    sniptext = "\n".join(lines[lastsep + 1 : lineid])
                    if pending_snippet.source is None:
                        pending_snippet.source = sniptext
                        self.snippets.append(pending_snippet)
                    elif pending_snippet.expect is None:
                        pending_snippet.expect = sniptext
                    elif pending_snippet.result is None:
                        pending_snippet.result = sniptext
                    else:
                        pass  # drop this piece
                lastsep = lineid

    def save(self):
        # Produce new text. Assign line numbers along the way
        linenr = 1
        newText = ""
        for snippet in self.snippets:
            text = snippet.toText()
            newText += text
            snippet.linenr = linenr
            linenr += text.count("\n")
        # Write only when the text has changed
        if newText != self.text:
            with open(self.filename, "wb") as f:
                f.write(newText.encode())


class Snippet:
    """Represents a snippet, consisting of at least two parts, the source, and the expected output."""

    def __init__(
        self, filename, linenr, action, title, source=None, expect=None, result=None
    ):
        # Meta data, just to repr the snippet better
        self.filename = filename
        self.linenr = linenr
        # Snippet info
        self.action = action
        self.title = title
        self.source = source
        self.expect = expect
        self.result = result

    def repr(self, showLine=True, *, clickableFilename=False):
        fname = self.filename
        if clickableFilename:  # in most (?) IDE's anyway
            fname = f'"{self.filename}"'
        else:
            fname = os.path.relpath(self.filename, config.rootDir)
        line = ""
        if showLine:
            line = f"line {self.linenr:<4}"
        return f"{fname} {line} - {self.action}: {self.title}"

    def toText(self):
        assert isinstance(self.source, str)
        lines = []

        # Source
        lines.append(f"{config.separator} {self.action}: {self.title}")
        lines.extend(self.source.split("\n"))
        ending = "end"
        # Expected and actual output
        if self.expect is None:
            if self.result is not None and not self.result:
                ending = "end (no output)"
            else:
                ending = "end (missing expected output)"
        elif self.result is None:
            lines.append(f"{config.separator} (expected) output")
            lines.extend(self.expect.split("\n"))
        elif self.expect == self.result:
            lines.append(f"{config.separator} output")
            lines.extend(self.expect.split("\n"))
        else:
            lines.append(f"{config.separator} expected output")
            lines.extend(self.expect.split("\n"))
            lines.append(f"{config.separator} actual output")
            lines.extend(self.result.split("\n"))
        # End sep and spacing
        lines.append(f"{config.separator} {ending}")
        lines.extend(["", "", "", ""])

        return "\n".join(lines)

    def run(self):
        assert isinstance(self.source, str)
        if self.action not in ACTIONS:
            raise RuntimeError(f"Unknown action: {self.action}")
        fun = ACTIONS[self.action]
        self.result = fun(self)
        return (self.expect or "") == self.result
