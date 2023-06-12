from . import tree

# todo: have primary and secondary labels, like Rust?
# todo: show a label after the ^^^ ?
# todo: colors!
# todo: allow annotating a larger code section (expression vs token)


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

    def getLineOfToken(self, token):
        lineIndex = token.line - self.source.lineOffset
        return self.source.lines[lineIndex]

    @property
    def hadError(self):
        return self.hadSyntaxError or self.hadAnalysisError or self.hadRuntimeError

    def syntaxError(self, errorCode, message, exprOrToken, explanation, **kwargs):
        """An error due to invalid syntax."""
        self.hadSyntaxError = True
        assert errorCode.startswith("E1") and len(errorCode) == 5
        self._show_error(
            "SyntaxError", errorCode, message, exprOrToken, explanation, **kwargs
        )

    def nameError(self, errorCode, message, exprOrToken, explanation, **kwargs):
        """An error generated while resolving names."""
        self.hadAnalysisError = True
        assert errorCode.startswith("E2") and len(errorCode) == 5
        self._show_error(
            "NameError", errorCode, message, exprOrToken, explanation, **kwargs
        )

    def runtimeError(self, errorCode, message, exprOrToken, explanation, **kwargs):
        """An error generated at runtime."""
        # self.print(f"[line {token.line}] Error : {message}")
        self.hadRuntimeError = True
        assert errorCode.startswith("E8") and len(errorCode) == 5
        self._show_error(
            "RuntimeError", errorCode, message, exprOrToken, explanation, **kwargs
        )

    def _show_error(
        self,
        errorType,
        errorCode,
        message,
        exprOrToken,
        explanation,
        includeTokens=(),
        linesBefore=0,
    ):
        lines = self.source.lines

        # Get bounds of code to show. Line numbers are relative.
        if isinstance(exprOrToken, tree.Expr):
            loc1, loc2 = exprOrToken.location()
            line1, column1 = loc1
            line2, column2 = loc2
        else:
            token = exprOrToken
            line1, column1 = token.line, token.column
            line2, column2 = line1, token.column + len(token.lexeme)

        # Get absolute line numbers (indices into the list of lines)
        lineIndex1 = line1 - self.source.lineOffset
        lineIndex2 = line2 - self.source.lineOffset

        # We may actually show more lines
        lineIndex3 = lineIndex1
        lineIndex4 = lineIndex2
        for _ in range(linesBefore):
            while not lines[lineIndex3].strip():  # skip empty lines
                lineIndex3 -= 1
            lineIndex3 -= 1
        for token in includeTokens:
            line = token.line - self.source.lineOffset
            lineIndex3 = min(lineIndex3, line)
            lineIndex4 = max(lineIndex4, line)

        charsForLineNo = len(str(lineIndex2 + 1))

        # Get Header
        link = f" {self.source.name}:{line1}"
        title = f"-- {errorType} ({errorCode}) "
        padding = 80 - max(0, len(title) + len(link))
        self.print(title + padding * "-" + link)

        # Message
        self.print(f"\n{message}\n")

        # Get code
        for lineIndex in range(lineIndex3, lineIndex4 + 1):
            lineno = str(lineIndex + 1).rjust(charsForLineNo)
            prefix1 = lineno + "| "
            prefix2 = " " * len(lineno) + "| "
            prefix3 = " " * len(prefix1)

            line = lines[lineIndex].rstrip()
            self.print(prefix1 + line)

            if lineIndex < lineIndex1:
                pass
            elif lineIndex == lineIndex1:
                if lineIndex1 == lineIndex2:
                    squigle = "^" * (column2 - column1)
                else:
                    squigle = "^" * (len(line) - column1)
                prefix = prefix3 if lineIndex == lineIndex2 else prefix2
                self.print(prefix + " " * (column1 - 1) + squigle)
            elif lineIndex < lineIndex2:
                squigle = "^" * len(line)
                self.print(prefix2 + squigle)
            elif lineIndex == lineIndex2:
                squigle = "^" * column1
                self.print(prefix2 + squigle)
            else:
                pass

        # Explanation
        self.print(explanation)
