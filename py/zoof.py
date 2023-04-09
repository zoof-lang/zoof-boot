# Stuff that I like:
#
# * Obviously feels familiar
# * Feels free
#
# Stuff I like less:
#
# * There may be an error in code paths that I don't cover.
# * A switch/match would be nice.
# * Proper enums would be nice

import sys

from lexer import Lexer
from printer import PrinterVisitor
from parser import Parser
from interpreter import InterpreterVisitor
from errors import ErrorHandler


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
        self.ehandler.setSource(source)

        lexer = Lexer(source)
        tokens = lexer.findTokens()

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


if __name__ == "__main__":
    argv = sys.argv.copy()
    if argv and argv[0].endswith("zoof.py"):
        argv.pop(0)

    c = ZoofCompiler()
    # c.main(argv)
    c.main(["../example.zf"])
