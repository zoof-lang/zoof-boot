import sys
from functools import partial

from .lexer import splitSource, tokenize
from .printer import PrinterVisitor
from .parser import Parser
from .interpreter import InterpreterVisitor
from .errors import ErrorHandler


class ZoofCompiler:
    def __init__(self, file=None):
        self.print = partial(print, file=file)
        self.ehandler = ErrorHandler(self.print)
        self.interpreter = InterpreterVisitor(self.print, self.ehandler)

    def runFile(self, path):
        with open(path, "rb") as f:
            source = f.read().decode()
        self.run(source)
        if self.ehandler.hadSyntaxError:
            sys.exit(65)
        elif self.ehandler.hadRuntimeError:
            sys.exit(70)

    def runPrompt(self):
        while True:
            line = input("zf> ")
            if not line:
                break
            self.run(line)
            self.ehandler.hadSyntaxError = False
            self.ehandler.hadRuntimeError = False

    def tokenize(self, source):
        lines = splitSource(source)
        self.ehandler.setSourceLines(lines)
        # todo: let the error handler construct the lines and filename from the tokens?
        return list(tokenize(lines))

    def parse(self, source):
        tokens = self.tokenize(source)
        parser = Parser(tokens, self.ehandler)
        return parser.parse()

    def run(self, source, out=None):
        statements = self.parse(source)
        if self.ehandler.hadSyntaxError:
            return

        # printer = PrinterVisitor()
        # for stmt in statements:
        #     printer.print(stmt)

        self.interpreter.interpret(statements)


def main(argv):
    c = ZoofCompiler()

    if len(argv) > 1:
        print("Usage zoofpyc [script]")
        sys.exit(64)
    elif len(argv) == 1:
        c.runFile(argv[0])
    else:
        c.runPrompt()
