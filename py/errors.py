class ErrorHandler:
    def __init__(self):
        self.lines = []
        self.hadError = False
        self.hadRuntimeError = False

    def setSource(self, source):
        self.lines = source.splitlines()

    def error(self, line, message):
        self.report(line, "", message)

    def syntaxError(self, token, message):
        """An error due to invalid syntax."""
        self._show_error(token, "SyntaxError: " + message)

    def analysisError(self, token, message):
        """An error generated by analysing the code."""
        self._show_error(token, "TypeError: " + message)

    def runtimeError(self, token, message):
        """An error generated at runtime."""
        # print(f"[line {token.line}] Error : {message}")
        self._show_error(token, "RuntimeError: " + message)
        self.hadRuntimeError = False

    def report(self, line, where, message):
        print(f"[line {line}] Error {where}: {message}")
        self.hadError = True

    def error_for_token(self, token, message):
        from lexer import TT

        if token.type == TT.EOF:
            self.report(token.line, " at end", message)
        else:
            self.report(token.line, "at '" + token.lexeme + "'", message)

    def _show_error(self, token, message):
        prefix = f"{token.line}| "
        print(message)
        print()
        print(prefix, self.lines[token.line - 1])
        print(" " * (len(prefix) + token.column) + "/\\")
