class ErrorHandler:
    def __init__(self, print):
        self.print = print
        self.source = None
        self.resetErrors()

    def swapSource(self, source):
        prev = self.source
        self.source = source
        return prev

    def resetErrors(self):
        self.hadSyntaxError = False
        self.hadAnalysisError = False
        self.hadRuntimeError = False

    @property
    def hadError(self):
        return self.hadSyntaxError or self.hadAnalysisError or self.hadRuntimeError

    def syntaxError(self, token, message):
        """An error due to invalid syntax."""
        self.hadSyntaxError = True
        self._show_error("SyntaxError", token, message)

    def nameError(self, token, message):
        """An error generated while resolving names."""
        self.hadAnalysisError = True
        self._show_error("NameError", token, message)

    def runtimeError(self, token, message):
        """An error generated at runtime."""
        # self.print(f"[line {token.line}] Error : {message}")
        self.hadRuntimeError = True
        self._show_error("RuntimeError", token, message)

    def _show_error(self, errorName, token, message):
        lines = self.source.lines
        lineIndex = token.line - self.source.lineOffset
        tokenName = str(token.type).split(".")[-1]
        prefix = f"{token.line}| "
        squigle = "^" * len(token.lexeme)
        self.print(f"In '{self.source.name}', line {token.line}")
        self.print(f"{errorName}: {message} at {repr(token.lexeme)} ({tokenName})")
        self.print()
        self.print(prefix + lines[lineIndex])
        self.print(" " * (len(prefix) + token.column - 1) + squigle)
