import enum


class TokenType(enum.Enum):
    LeftParen = 1
    RightParen = 2
    LeftBrace = 3
    RightBrace = 4
    Comma = 5
    Dot = 6
    Minus = 7
    Plus = 8
    Semicolon = 9
    Slash = 10
    Star = 11

    Bang = 12
    BangEqual = 13
    Equal = 14
    EqualEqual = 15
    Greater = 16
    GreaterEqual = 17
    Less = 18
    LessEqual = 19

    Identifier = 20
    Keyword = 200
    String = 21
    Number = 22

    And = 23
    Class = 24
    Else = 25
    Falsey = 26
    Fun = 27
    For = 28
    If = 29
    Nil = 30
    Or = 31
    Print = 32
    Return = 33
    Super = 34
    This = 35
    Truey = 36
    Var = 37
    While = 38

    EOF = 39


TT = TokenType


##

KEYWORDS = "and", "import", "or", "and", "fun"


class Token:
    def __init__(self, type, lexeme, literal, line):
        self.type = type
        self.lexeme = lexeme
        self.literal = literal
        self.line = line

    def __repr__(self):
        stype = str(self.type).split(".")[1]
        return f"<Token {stype} {self.lexeme!r}>"


class Scanner:
    def __init__(self, source, errorHandler):
        self.source = source
        self.errorHandler = errorHandler
        self.tokens = []

        self.start = 0
        self.current = 0
        self.line = 1

    def scanTokens(self):
        while not self.isAtEnd():
            self.start = self.current
            self.scanToken()

        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    def isAtEnd(self):
        return self.current >= len(self.source)

    def advance(self):
        c = self.source[self.current]
        self.current += 1
        return c

    def addToken(self, type, literal=None):
        text = self.source[self.start : self.current]
        self.tokens.append(Token(type, text, literal, self.line))

    def match(self, expected):
        # Conditional advance
        if self.isAtEnd():
            return False
        if self.source[self.current] != expected:
            return False
        else:
            self.current += 1
            return True

    def peek(self):
        # Lookahead
        if self.isAtEnd():
            return "\0"
        else:
            return self.source[self.current]

    def peekNext(self):
        # Lookahead two chars
        if self.current + 1 >= len(self.source):
            return "\0"
        else:
            return self.source[self.current + 1]

    def scanToken(self):
        c = self.advance()

        # Single chars
        if c == "(":
            self.addToken(TT.LeftParen)
        elif c == ")":
            self.addToken(TT.RightParen)
        elif c == "{":
            self.addToken(TT.LeftBrace)
        elif c == "}":
            self.addToken(TT.RightBrace)
        elif c == ",":
            self.addToken(TT.Comma)
        elif c == ".":
            self.addToken(TT.Dot)
        elif c == "-":
            self.addToken(TT.Minus)
        elif c == "+":
            self.addToken(TT.Plus)
        elif c == "*":
            self.addToken(TT.Star)
        # Operators
        elif c == "!":
            self.addToken(TT.BangEqual if self.match("=") else TT.Bang)
        elif c == "=":
            self.addToken(TT.EqualEqual if self.match("=") else TT.Equal)
        elif c == "<":
            self.addToken(TT.LessEqual if self.match("=") else TT.Less)
        elif c == ">":
            self.addToken(TT.GreaterEqual if self.match("=") else TT.Greater)
        # Longer ones
        elif c == "/":
            if self.match("/"):
                while self.peek() != "\n" and not self.isAtEnd():
                    self.advance()
            else:
                self.addToken(TT.Slash)
        elif c in " \t\r":
            pass  # whitespace
        elif c == "\n":
            self.line += 1
        # Literals
        elif c == "'":
            self.handleString()
        elif isNumeric(c):
            self.handleNumber()
        elif isAlpha(c):
            self.handleIdentifier()
        # Fail!
        else:
            self.errorHandler.error(self.line, f"Unexpected character: '{c}'")

    def handleString(self):
        while self.peek() != "'" and not self.isAtEnd():
            if self.peek() == "\n":
                self.line += 1
                # todo: dont allow multilie for normal strings
            self.advance()

        if self.isAtEnd():
            self.errorHandler.error(self.line, "Unterminated string.")
            return

        # Move past the closing quote char
        self.advance()

        value = self.source[self.start + 1 : self.current - 1]
        self.addToken(TT.String, value)

    def handleNumber(self):
        while isNumeric(self.peek()):
            self.advance()

        # Consume a dot, and digits after it
        hasDot = False
        if self.peek() == "." and isNumeric(self.peekNext()):
            hasDot = True
            self.advance()
            while isNumeric(self.peek()):
                self.advance()

        s = self.source[self.start : self.current]
        value = float(s) if hasDot else int(s)
        self.addToken(TT.Number, value)

    def handleIdentifier(self):
        while isAlphaNumeric(self.peek()):
            self.advance()

        name = self.source[self.start : self.current]
        if name in KEYWORDS:
            self.addToken(TT.Keyword)
        else:
            self.addToken(TT.Identifier)


def isNumeric(c):
    return c in "0123456789"


def isAlpha(c):
    return c.isalpha() or c == "_"


def isAlphaNumeric(c):
    return c.isalpha() or c in "_0123456789"
