import errors

type 
  TokenType = enum
    LeftParen,
    RightParen,
    LeftBrace,
    RightBrace,
    Comma ,
    Dot ,
    Minus, 
    Plus ,
    Semicolon, 
    Slash ,
    Star,

    Bang ,
    BangEqual, 
    Equal,   
    EqualEqual, 
    Greater, 
    GreaterEqual, 
    Less, 
    LessEqual, 

    Identifier, 
    Keyword, 
    String, 
    Number, 
    EOF,


const KEYWORDS = ["and", "import", "or", "and", "fun"]

type Token = object
    typ: TokenType
    lexeme:string
    line:int
    #literal:auto

type Scanner* = object
    source*: string
    handler*: ErrorHandler
    tokens*: seq[Token]
    start*: int
    current*: int
    line*: int

proc newScanner* (source: string, handler: ErrorHandler): Scanner = 
    return Scanner(source: source, handler: handler, tokens: @[], start: 0, current: 0, line: 1)

proc isAtEnd(self: Scanner) : bool =
    return self.current >= self.source.len

proc advance(s: Scanner) : char =
    #let c = self.source[self.current]
    s.current += 1
    #return c
    return s.source[s.current - 1]

proc scanToken(self: Scanner) =
    let c = self.advance()
    echo c

proc scanTokens*(self: var Scanner) : seq[Token] = 

    while not self.isAtEnd:
        self.start = self.current
        self.scanToken()
    
    var token = Token(typ:EOF, lexeme:"EOF", line:self.line)
    self.tokens.add(token)
    return self.tokens

