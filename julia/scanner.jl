

@enum TokenType begin
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
    String_ = 21
    Number = 22

    EOF = 39
end

KEYWORDS = ["and", "import", "or", "and", "fun"]

struct Token
    type :: TokenType
    lexeme :: String
    line :: Int64
    literal :: Any
end


mutable struct Scanner        
    source :: String
    handler #:: ErrorHandler we'd need to put the ErrorHandler in a separate module that both main.jl and scanner.jl can include/import
    tokens :: Vector{Token}

    start :: Int64
    current :: Int64
    line :: Int64
end

function Scanner(source::String, handler)
    Scanner(source, handler, [], 1, 1, 1)
end

function scanTokens(scanner::Scanner)
    while !isAtEnd(scanner)
        scanner.start = scanner.current
        scanToken(scanner)
    end
    token = Token(EOF, "EOF", scanner.line, missing)
    push!(scanner.tokens, token)
    return scanner.tokens
end

function isAtEnd(scanner::Scanner) 
    scanner.current > length(scanner.source)
end

function advance(scanner::Scanner) :: Char
    c  = scanner.source[scanner.current]
    scanner.current += 1
    return c
end

function peek(scanner::Scanner)
    if isAtEnd(scanner)
        "\0"
    else
        scanner.source[scanner.current]
    end
end

function peekNext(scanner::Scanner)
    if scanner.current + 1 > length(scanner.source)
        return "\0"
    else
        scanner.source[scanner.current+1]
    end
end

function match(scanner::Scanner, expected::Char)
    if isAtEnd(scanner)
        false
    elseif scanner.source[scanner.current] != expected
        false
    else
        scanner.current += 1
        true
    end
end

function addToken(scanner::Scanner, typ :: TokenType)
    lexeme = scanner.source[scanner.start: scanner.current-1]
    token = Token(typ, lexeme, scanner.line, missing)
    push!(scanner.tokens, token)
end

function addToken(scanner::Scanner, typ :: TokenType, literal::Any)
    lexeme = scanner.source[scanner.start: scanner.current-1]
    token = Token(typ, lexeme, scanner.line, literal)
    push!(scanner.tokens, token)
end

function scanToken(scanner::Scanner)
    c = advance(scanner)

    # Whitespace
    if c == ' ' || c == '\t' || c == '\r'
    elseif c == '\n'
        scanner.line += 1
    # Single chars
    elseif c == '('
        addToken(scanner, LeftParen)
    elseif c == ')'
        addToken(scanner, RightParen)
    elseif c == '{'
        addToken(scanner, LeftBrace)
    elseif c == '}'
        addToken(scanner, RightBrace)
    elseif c == ','
        addToken(scanner, Comma)
    elseif c == '.'
        addToken(scanner, Dot)
    elseif c == '-'
        addToken(scanner, Minus)
    elseif c == '+'
        addToken(scanner, Plus)
    elseif c == '*'
        addToken(scanner, Star)
    # Operators
    elseif c == '!'
        addToken(scanner, match(scanner, '=') ? BangEqual : Bang)
    elseif c == '='
        addToken(scanner, match(scanner, '=') ? EqualEqual : Equal)
    elseif c == '<'
        addToken(scanner, match(scanner, '=') ? LessEqual : Less)
    elseif c == '>'
        addToken(scanner, match(scanner, '=') ? GreaterEqual : Greater)
    # Longer
    elseif c == '/'
        if match(scanner, '/')
            while peek(scanner) != '\n' && !isAtEnd(scanner)
                advance(scanner)
            end
        else
            addToken(scanner, Slash)
        end
    # Literals
    elseif c == '\''
        handleString(scanner)
    elseif isNumeric(c)
        handleNumber(scanner)
    elseif isAlpha(c)
        handleIdentifier(scanner)
    # Fail
    else
        error(scanner.handler, scanner.line, "Unexpected character '$c'")
    end
end

function isNumeric(c::Char)
    isdigit(c)
end

function isAlpha(c::Char)
    isletter(c)
end

function isAlphaNumeric(c::Char)
    isdigit(c) || isletter(c)
end

function handleString(scanner::Scanner)
    while peek(scanner) != '\'' && !isAtEnd(scanner)
        if peek(scanner) == '\n'
            scanner.line += 1
        end
        advance(scanner)
    end

    if isAtEnd(scanner)
        error(scanner.handler, scanner.line, "Unterminated string.")
        return
    end

    advance(scanner)  # Move past the closing quote char

    value = scanner.source[scanner.start + 1 : scanner.current - 2]
    addToken(scanner, String_, value)
end

function handleNumber(scanner::Scanner)
    while isdigit(peek(scanner))
        advance(scanner)
    end
    # Consume a dot, and digits after it
    hasDot = false
    if peek(scanner) == '.' && isdigit(peekNext(scanner))
        hasDot = true
        advance(scanner)
        while isdigit(peek(scanner))
            advance(scanner)
        end
    end

    s = scanner.source[scanner.start : scanner.current-1]
    value = hasDot ? parse(Float64, s) : parse(Int64, s)
    addToken(scanner, Number, value)
end

function handleIdentifier(scanner::Scanner)
    while isAlphaNumeric(peek(scanner))
        advance(scanner)
    end

    name = scanner.source[scanner.start : scanner.current-1]
    if name in KEYWORDS
        addToken(scanner, Keyword)
    else
        addToken(scanner, Identifier)
    end
end