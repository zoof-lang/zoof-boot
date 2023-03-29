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
from printer import AstPrinter
from parser import Parser


class ZoofCompiler:
    def __init__(self):
        self.errorHandler = ErrorHandler()

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
        if self.errorHandler.hadError:
            sys.exit(65)

    def runPrompt(self):
        while True:
            line = input("zf> ")
            if not line:
                break
            self.run(line)
            self.errorHandler.hadError = False

    def run(self, source):
        lexer = Lexer(source, self.errorHandler)
        tokens = lexer.findTokens()

        # for token in tokens:
        #     print(token)

        parser = Parser(tokens, self.errorHandler)
        expr = parser.parse()
        if self.errorHandler.hadError:
            return

        printer = AstPrinter()
        printer.print(expr)


class ErrorHandler:
    def __init__(self):
        self.hadError = False

    def error(self, line, message):
        self.report(line, "", message)

    def report(self, line, where, message):
        print(f"[line {line}] Error {where}: {message}")
        self.hadError = True

    def error_for_token(self, token, message):
        from lexer import TT

        if token.type == TT.EOF:
            self.report(token.line, " at end", message)
        else:
            self.report(token.line, "at '" + token.lexeme + "'", message)


if __name__ == "__main__":
    c = ZoofCompiler()
    # c.main(sys.argv)
    c.main([])
    # c.main(["../syntax/syntax1.zf"])
