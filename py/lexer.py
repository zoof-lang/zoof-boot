from tokens import TT, KEYWORDS, RESERVED, Token


class Lexer:
    """A scanner, or lexer, call it what you want, but it gets the job done.
    It wont't ever show errors, it will simply emit failure tokens.
    """

    def __init__(self, source):
        self.source = source
        self.tokens = []

        self.start = 0
        self.current = 0
        self.line = 1
        self.lineOffset = -1

    def findTokens(self):
        while not self.isAtEnd():
            self.start = self.current
            self.findToken()

        self.tokens.append(Token(TT.EOF, "", self.line, self.start - self.lineOffset))
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
        if type == TT.Invalid:
            if len(self.tokens) > 0 and self.tokens[-1].type == TT.Invalid:
                self.tokens[-1].lexeme += text
                return
        self.tokens.append(Token(type, text, self.line, self.start - self.lineOffset))

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
                self.addToken(TT.Invalid)
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
            self.addToken(TT.Invalid)

    def handleString(self):
        unterminated = False
        while self.peek() != "'":
            if self.isAtEnd():
                unterminated = True
                break
            elif self.peek() == "\n":
                unterminated = True
                break
            self.advance()

        if unterminated:
            self.addToken(TT.LiteralUnterminatedString)
            self.advance()
        else:
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
