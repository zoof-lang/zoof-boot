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
    Invalid = 72
    LiteralUnterminatedString = 73

    EOF = 99


TT = TokenType


##

KEYWORDS = (
    "import",
    "from",
    "as",
    "and",
    "or",
    "fun",
    "return",
    "if",
    "elseif",
    "then",
    "do",
    "for",
    "while",
)
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
