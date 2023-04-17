import enum


class TokenType(enum.Enum):
    LeftParen = 11
    RightParen = 12
    LeftBrace = 13
    RightBrace = 14

    Comma = 21
    Dot = 22
    DotDot = 23
    Ellipsis = 24
    Semicolon = 25
    Colon = 26
    Tilde = 27

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
    LiteralNil = 65

    Comment = 71
    Newline = 72
    Indent = 73
    Dedent = 74

    Invalid = 81
    LiteralUnterminatedString = 82
    InvalidIndentation = 83

    EOF = 99


TT = TokenType


##

KEYWORDS = (
    "print",
    "import",
    "from",
    "as",
    "and",
    "or",
    "fun",
    "return",
    "if",
    "elif",
    "elseif",
    "else",
    "then",
    "for",
    "in",
    "while",
    "do",
    "loop",
    "over",
)
RESERVED = "super", "this", "swicth", "match"


class Token:
    def __init__(self, type, lexeme, line, column):
        self.type = type
        self.lexeme = lexeme
        self.line = line
        self.column = column

    def __repr__(self):
        return f"<Token {self.typename} {self.lexeme!r} ({self.line}:{self.column})>"

    @property
    def typename(self):
        return str(self.type).split(".")[1]