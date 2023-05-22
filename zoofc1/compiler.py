import sys
from functools import partial

from .lexer import splitSource, tokenize
from .printer import PrinterVisitor
from .parser import Parser
from .resolver import ResolverVisitor
from .interpreter import InterpreterVisitor
from .errors import ErrorHandler


"""
With a normal string you have 1 byte per char (assuming mostlty ansi chars).

We can put tokens in a big global list, so the token only needs an index in the list to get the full lexeme.
Or rather, we can just cache tokens and reuse them, so there is only one kind.
Is this worth it for code that is heavily documented and commented?

Each token requires:
- lexeme, can actually encode the type, in many cases just a ref (8 bytes)
- column 2 or 4 bytes
- reference to filename and full source
- link to next (8 bytes)

- One big string, either the original, or a packed one without duplicating tokens.
- Array of tokens, just 8 bytes each:
  - type 2 bytes
  - index of start position in array 2 bytes
  - length 2 bytes
  - column 2 bytes

"""

# def tokenize_code(text):
#     """Turn source code into a list of tokens."""
#     # Note: this can be refactored to be a generator, for streamed parsing
#     lines = splitSource(text)
#     return list(tokenize(lines))


# def parse(text):
#     tokens = self.tokenize(source)
#     parser = Parser(tokens, self.ehandler)
#     return parser.parse()


class Source:
    """An object that represents a piece of source code.

    Typically a module is defined with one Source (the complete code),
    but sometimes blocks are added incrementally, the most common
    use-case being an interactive session.
    """

    # This object is intended to be lightweight, to hold the (file)
    # name and line offset, as well as a textual representation, so
    # that the error handler can produce a nice message.
    #
    # I suppose later on the textual representation could be lazily
    # loaded to reduce memory.
    #
    # This object gets passed around when parsing, analysing, and
    # interpreting code, and is then dropped, except if ...
    #
    # Functions defined in this code will get a reference to this object
    # (when the definition executes), so that when that function is
    # called, error handling can still occur.

    def __init__(self, name, lineOffset, text):
        self.name = name
        self.lineOffset = lineOffset
        self.lines = splitSource(text)


class Program:
    """Object to hold together the source and the ast statements."""

    def __init__(self, source, statements):
        self.source = source
        self.statements = statements


class Module:
    """An object that represents a module - a context that represents
    a global scope.

    Modules can (when I've implemented it) import stuff from one
    another. Imported files are represented by modules, but there is
    also the main module in an interactive session, and there can be
    more in-memory modules.
    """

    def __init__(self, name, compiler):
        self.name = name
        self.compiler = compiler
        self.sources = []
        self.environment = None

    def tokenize(self, source):
        assert isinstance(source, Source)
        return list(tokenize(source.lines))

    def parse(self, source):
        assert isinstance(source, Source)
        tokens = self.tokenize(source)
        statements = self.compiler.parser.parse(source, tokens)
        return Program(source, statements)

    def execute(self, source):
        assert isinstance(source, Source)
        program = self.parse(source)

        if self.compiler.ehandler.hadSyntaxError:
            return

        # printer = PrinterVisitor()
        # for stmt in statements:
        #     printer.print(stmt)

        self.compiler.resolver.resolve_program(program)
        # todo: distiguish between different kinds of errors
        if self.compiler.ehandler.hadSyntaxError:
            return

        self.compiler.interpreter.interpret(program)


class ZoofCompiler:
    """This class represents one Zoof "instance", whatever that means.
    It will likely represent one process running Zoof. Though in theory
    there could be multiple interpreters that operate independently.

    The tokenizer can lex each code input individually. The parser can
    also just do its thing on each incoming code. But the resolver needs
    a persistent tree that grows as new code is run. The same goes for
    future subsequent passes. The interpreter needs to maintain the
    program's state and adjust it as new code is run.
    """

    def __init__(self, file=None):
        self.modules = {}

        self.print = partial(print, file=file)
        self.ehandler = ErrorHandler(self.print)
        self.parser = Parser(self.ehandler)
        self.resolver = ResolverVisitor(self.ehandler)
        self.interpreter = InterpreterVisitor(self.print, self.ehandler)

    def createModule(self, name):
        module = Module(name, self)
        self.modules[module.name] = module
        return module

    def runFile(self, path):
        with open(path, "rb") as f:
            text = f.read().decode()
        source = Source(path, 1, text)
        module = self.createModule("main")
        module.execute(source)
        if self.ehandler.hadSyntaxError:
            sys.exit(65)
        elif self.ehandler.hadRuntimeError:
            sys.exit(70)

    def runPrompt(self):
        mainModule = createModule("main")
        inputCount = 1
        while True:
            line = input(f"zf {inputCount}> ")
            inputCount += 1
            if not line:
                break
            source = Source(f"input {inputCount}", 1, line)
            mainModule.execute(source)
            # todo: add a reset method of some kind?
            self.ehandler.hadSyntaxError = False
            self.ehandler.hadRuntimeError = False


def main(argv):
    c = ZoofCompiler()

    if len(argv) > 1:
        print("Usage zoofpyc [script]")
        sys.exit(64)
    elif len(argv) == 1:
        c.runFile(argv[0])
    else:
        c.runPrompt()
