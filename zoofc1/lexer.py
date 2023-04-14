from .tokens import TT, KEYWORDS, RESERVED, Token


def splitSource(source):
    """Split the source in lines. Always ends with an empty line."""
    lines = source.splitlines(False)
    if not lines or lines[-1] != "":
        lines.append("")
    return lines


def tokenize(lines):
    lexer = Lexer(0)
    for line in lines:
        yield from lexer.processLine(line)
    yield from lexer.finish()


class Lexer:
    """A scanner, lexer, tokenizer, call it what you want, but it gets the job done.
    It wont't ever show errors, it will simply emit failure tokens.
    """

    def __init__(self, lineOffset=0):
        self.lineNr = lineOffset
        self.wcs = [0]  # whitespace counts (for indentation)

    def processLine(self, line):
        self.source = line
        self.lineNr += 1
        self.start = 0
        self.current = 0

        # Find the first token
        token = self.findToken()

        # todo: also handle whole source being indented
        # Handle indent / dedent
        if token.type not in (TT.Newline, TT.Comment):
            wc = token.column - 1
            if wc > self.wcs[-1]:
                self.wcs.append(wc)
                yield Token(TT.Indent, self.source[:wc], self.lineNr, 1)
            elif wc < self.wcs[-1]:
                dedentCount = 0
                while wc < self.wcs[-1]:
                    self.wcs.pop(-1)
                    dedentCount += 1
                if wc == self.wcs[-1]:
                    for _ in range(dedentCount):
                        yield Token(TT.Dedent, self.source[:wc], self.lineNr, 1)
                else:
                    yield Token(TT.InvalidIndentation, self.source[:wc], self.lineNr, 1)

        # Find remaining tokens on this line
        yield token
        while token.type != TT.Newline:
            token = self.findToken()
            yield token

    def finish(self):
        # Flush the indentation stack
        while len(self.wcs) > 1:
            i = self.wcs.pop(-1)
            yield Token(TT.Dedent, " " * i, self.lineNr, 1)

        # Mark end
        yield Token(TT.EOF, "", self.lineNr, 1)

    def isAtEnd(self):
        return self.current >= len(self.source)

    def advance(self):
        if self.current < len(self.source):
            c = self.source[self.current]
            self.current += 1
            return c
        else:
            return "\n"

    def peek(self):
        if self.current >= len(self.source):
            return "\n"
        else:
            return self.source[self.current]

    def peekNext(self):
        if self.current + 1 >= len(self.source):
            return "\n"
        else:
            return self.source[self.current + 1]

    def moveToEOL(self):
        self.current = len(self.source)

    def match(self, expected):
        # Conditional advance
        if self.peek() == expected:
            self.advance()
            return True
        else:
            return False

    def findToken(self):
        # Skip whitespace
        while self.peek() in " \t":
            self.advance()

        # Detect the token
        self.start = self.current
        tokenType = self.identifyToken()

        # Create it
        lexeme = self.source[self.start : self.current]
        return Token(tokenType, lexeme, self.lineNr, self.start + 1)

    def identifyToken(self):
        c = self.advance()

        # Newline and comments
        if c == "\n":
            return TT.Newline
        elif c == "#":
            self.moveToEOL()
            return TT.Comment
        # Single chars
        elif c == "(":
            return TT.LeftParen
        elif c == ")":
            return TT.RightParen
        elif c == "{":
            return TT.LeftBrace
        elif c == "}":
            return TT.RightBrace
        elif c == ",":
            return TT.Comma
        elif c == ";":
            return TT.Semicolon
        elif c == ":":
            return TT.Colon
        elif c == ".":
            ndots = 1
            if self.match("."):
                ndots += 1
                if self.match("."):
                    ndots += 1
            return [None, TT.Dot, TT.DotDot, TT.Ellipsis][ndots]
        elif c == "~":
            return TT.Tilde
        elif c == "-":
            return TT.Minus
        elif c == "+":
            return TT.Plus
        elif c == "*":
            return TT.Star
        elif c == "/":
            return TT.Slash
        elif c == "^":
            return TT.Caret
        # Operators
        elif c == "!":
            if self.match("="):
                return TT.BangEqual
            else:
                return TT.Invalid
        elif c == "=":
            return TT.EqualEqual if self.match("=") else TT.Equal
        elif c == "<":
            return TT.LessEqual if self.match("=") else TT.Less
        elif c == ">":
            return TT.GreaterEqual if self.match("=") else TT.Greater
        # Literals
        elif c == "'":
            return self.handleString()
        elif isNumeric(c):
            return self.handleNumber()
        elif isAlpha(c):
            return self.handleIdentifier()
        # Fail!
        else:
            return TT.Invalid

    def handleString(self):
        c = self.advance()
        while c not in "'\n":
            c = self.advance()

        if c == "\n":
            return TT.LiteralUnterminatedString
        else:
            return TT.LiteralString

    def handleNumber(self):
        while isNumeric(self.peek()):
            self.advance()

        # Consume a dot, and digits after it
        if self.peek() == "." and isNumeric(self.peekNext()):
            self.advance()
            while isNumeric(self.peek()):
                self.advance()

        return TT.LiteralNumber

    def handleIdentifier(self):
        while isAlphaNumeric(self.peek()):
            self.advance()

        name = self.source[self.start : self.current]
        if name in KEYWORDS:
            return TT.Keyword
        elif name in RESERVED:
            return TT.Reserved
        elif name == "true":
            return TT.LiteralTrue
        elif name == "false":
            return TT.LiteralFalse
        elif name == "nil":
            return TT.LiteralNil
        else:
            return TT.Identifier


def isNumeric(c):
    return c in "0123456789"


def isAlpha(c):
    return c.isalpha() or c == "_"


def isAlphaNumeric(c):
    return c.isalpha() or c in "_0123456789"
