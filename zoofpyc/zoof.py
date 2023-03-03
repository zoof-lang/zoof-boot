import sys

from .scanner import Scanner


class ZoofCompiler:
    def __init__(self):
        self.errorHandler = ErrorHandler()

    def main(self):
        if len(sys.argv) > 1:
            print("UsageL zoofpyc [script]")
            sys.exit(64)
        elif len(sys.argv) == 1:
            self.runFile(sys.argv[0])
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
        scanner = Scanner(source, self.errorHandler)
        tokens = scanner.scanTokens()

        for token in tokens:
            print(token)


class ErrorHandler:
    def __init__(self):
        self.hadError = False

    def error(self, line, message):
        self.report(line, "", message)

    def report(self, line, where, message):
        print(f"[line {line}] Error {where}: {message}")
        self.hadError = True
