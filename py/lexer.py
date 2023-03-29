import enum


class TokenType(enum.Enum):

    LeftParen = 11
    RightParen = 12
    LeftBrace = 13
    RightBrace = 14

    Comma = 21
    Dot = 22
    Ellipsis = 23  # Or just track dots?
    Semicolon = 24
    Colon = 25
    Tilde = 26

    Minus = 31
    Plus = 32
    Star = 33
    Slash = 34
    Caret = 35

    BangEqual = 42
    Equal = 43
    EqualEqual = 44
    Greater = 45
    GreaterEqual = 46
    Less = 47
    LessEqual = 48

    Identifier = 51
    Keyword = 52
    Reserved = 53

    LiteralString = 61
    LiteralNumber = 62
    LiteralFalse = 63
    LiteralTrue = 64
    LiteralNul = 65

    Comment = 71

    EOF = 99


TT = TokenType


##

KEYWORDS = "import", "from", "as", "and", "or", "fun", "return", "if", "elseif", "then", "do", "for", "while",
RESERVED = "super", "this", "swicth", "match"


class Token:
    def __init__(self, type, lexeme, line, column):
        self.type = type
        self.lexeme = lexeme
        self.line = line
        self.column = column

    def __repr__(self):
        stype = str(self.type).split(".")[1]
        return f"<Token {stype} {self.lexeme!r} ({self.line}:{self.column})>"


class Lexer:
    def __init__(self, source, errorHandler):
        self.source = source
        self.errorHandler = errorHandler
        self.tokens = []

        self.start = 0
        self.current = 0
        self.line = 1
        self.lineOffset = -1

    def findTokens(self):
        while not self.isAtEnd():
            self.start = self.current
            self.findToken()

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.start - self.lineOffset))
        return self.tokens

    def isAtEnd(self):
        return self.current >= len(self.source)

    def advance(self):
        c = self.source[self.current]
        self.current += 1
        return c

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

    def match(self, expected):
        # Conditional advance
        if self.isAtEnd():
            return False
        if self.source[self.current] != expected:
            return False
        else:
            self.current += 1
            return True

    def addToken(self, type):
        text = self.source[self.start : self.current]
        self.tokens.append(Token(type, text, self.line, self.start- self.lineOffset))

    def findToken(self):
        c = self.advance()
        # Witespace and comments
        if c == "\n":
            self.line += 1
            self.lineOffset = self.current - 1
        elif c in " \t\r":
            pass
        elif c == "#":
            while self.peek() != "\n" and not self.isAtEnd():
                self.advance()
            self.addToken(TT.Comment)
        # Single chars
        elif c == "(":
            self.addToken(TT.LeftParen)
        elif c == ")":
            self.addToken(TT.RightParen)
        elif c == "{":
            self.addToken(TT.LeftBrace)
        elif c == "}":
            self.addToken(TT.RightBrace)
        elif c == ",":
            self.addToken(TT.Comma)
        elif c == ";":
            self.addToken(TT.Semicolon)
        elif c == ":":
            self.addToken(TT.Colon)
        elif c == ".":
            self.addToken(TT.Dot)
        elif c == "~":
            self.addToken(TT.Tilde)
        elif c == "-":
            self.addToken(TT.Minus)
        elif c == "+":
            self.addToken(TT.Plus)
        elif c == "*":
            self.addToken(TT.Star)
        elif c == "/":
            self.addToken(TT.Slash)
        elif c == "^":
            self.addToken(TT.Caret)
        # Operators
        elif c == "!":
            if self.match("="):
                self.addToken(TT.BangEqual)
            else:
                self.error(f"Expected '=' after '!', use 'not' for logical negation.")
        elif c == "=":
            self.addToken(TT.EqualEqual if self.match("=") else TT.Equal)
        elif c == "<":
            self.addToken(TT.LessEqual if self.match("=") else TT.Less)
        elif c == ">":
            self.addToken(TT.GreaterEqual if self.match("=") else TT.Greater)
        # Literals
        elif c == "'":
            self.handleString()
        elif isNumeric(c):
            self.handleNumber()
        elif isAlpha(c):
            self.handleIdentifier()
        # Fail!
        else:
            self.error(f"Unexpected character: '{c}'")

    def error(self, message):
        self.errorHandler.error(self.line, message)

    def handleString(self):
        while self.peek() != "'" and not self.isAtEnd():
            if self.peek() == "\n":
                self.line += 1
                # todo: dont allow multiline for normal strings
            self.advance()

        if self.isAtEnd():
            self.errorHandler.error(self.line, "Unterminated string.")
            return

        # Move past the closing quote char
        self.advance()
        self.addToken(TT.LiteralString)

    def handleNumber(self):
        while isNumeric(self.peek()):
            self.advance()

        # Consume a dot, and digits after it
        if self.peek() == "." and isNumeric(self.peekNext()):
            self.advance()
            while isNumeric(self.peek()):
                self.advance()

        self.addToken(TT.LiteralNumber)

    def handleIdentifier(self):
        while isAlphaNumeric(self.peek()):
            self.advance()

        name = self.source[self.start : self.current]
        if name in KEYWORDS:
            self.addToken(TT.Keyword)
        elif name in RESERVED:
            self.addToken(TT.Reserved)
        elif name == "true":
            self.addToken(TT.LiteralTrue)
        elif name == "false":
            self.addToken(TT.LiteralFalse)
        elif name == "nil":
            self.addToken(TT.LiteralNil)
        else:
            self.addToken(TT.Identifier)


def isNumeric(c):
    return c in "0123456789"


def isAlpha(c):
    return c.isalpha() or c == "_"


def isAlphaNumeric(c):
    return c.isalpha() or c in "_0123456789"
