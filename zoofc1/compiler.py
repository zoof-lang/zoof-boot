import sys

from .lexer import splitSource, tokenize
from .printer import PrinterVisitor
from .parser import Parser
from .interpreter import InterpreterVisitor
from .errors import ErrorHandler


class ZoofCompiler:
    def __init__(self):
        self.ehandler = ErrorHandler()
        self.interpreter = InterpreterVisitor(self.ehandler)

    def main(self, argv):
        if len(argv) > 1:
            print("Usage zoofpyc [script]")
            sys.exit(64)
        elif len(argv) == 1:
            self.runFile(argv[0])
        else:
            self.runPrompt()

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

    def run(self, source):
        lines = splitSource(source)

        self.ehandler.setSourceLines(lines)

        tokens = list(tokenize(lines))

        # for token in tokens:
        #     print(token)

        parser = Parser(tokens, self.ehandler)
        statements = parser.parse()
        if self.ehandler.hadSyntaxError:
            return

        # printer = PrinterVisitor()
        # for stmt in statements:
        #     printer.print(stmt)
        self.interpreter.interpret(statements)
