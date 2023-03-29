package main

import (
	"fmt"
	"strconv"
)

type TokenType int

const (
	LeftParen  = 1
	RightParen = 2
	LeftBrace  = 3
	RightBrace = 4
	Comma      = 5
	Dot        = 6
	Minus      = 7
	Plus       = 8
	Semicolon  = 9
	Slash      = 10
	Star       = 11

	Bang         = 12
	BangEqual    = 13
	Equal        = 14
	EqualEqual   = 15
	Greater      = 16
	GreaterEqual = 17
	Less         = 18
	LessEqual    = 19

	Identifier = 20
	Keyword    = 200
	String     = 21
	Number     = 22

	And    = 23
	Class  = 24
	Else   = 25
	Falsey = 26
	Fun    = 27
	For    = 28
	If     = 29
	Nil    = 30
	Or     = 31
	Print  = 32
	Return = 33
	Super  = 34
	This   = 35
	Truey  = 36
	Var    = 37
	While  = 38

	EOF = 39
)

var KEYWORDS = []string{
	"and",
	"class",
	"else",
	"for",
	"fun",
	"if",
	"nil",
	"or",
	"print",
	"return",
	"super",
	"this",
	"var",
	"while",
}

func stringIsKeyword(a string) bool {
	for _, b := range KEYWORDS {
		if b == a {
			return true
		}
	}
	return false
}

type Token struct {
	typ     TokenType
	lexeme  string
	literal interface{}
	line    int
}

func NewToken(tt TokenType, lexeme string, literal interface{}, line int) *Token {
	return &Token{tt, lexeme, literal, line}
}

func (token *Token) ToString() string {
	var suffix string
	switch v := token.literal.(type) {
	case int64:
		suffix = " -> " + fmt.Sprint(v)
	case float64:
		suffix = " -> " + fmt.Sprint(v)
	case string:
		suffix = " -> '" + v + "'"
	default:
		suffix = ""
	}
	return "Token " + string(token.typ) + " '" + token.lexeme + "' on line " + strconv.Itoa(token.line) + suffix
}

// -----

type Scanner struct {
	source  string
	handler ErrorHandler
	tokens  []Token
	start   int
	current int
	line    int
}

func NewScanner(source string, handler ErrorHandler) *Scanner {
	var tokens []Token
	return &Scanner{source, handler, tokens, 0, 0, 1}
}

func (scanner *Scanner) scanTokens() []Token {

	for !scanner.isAtEnd() {
		scanner.start = scanner.current
		scanner.scanToken()
	}
	scanner.tokens = append(scanner.tokens, Token{EOF, "EOF", nil, scanner.line})
	return scanner.tokens
}

func (scanner *Scanner) isAtEnd() bool {
	return scanner.current >= len(scanner.source)
}

func (scanner *Scanner) advance() byte {
	c := scanner.source[scanner.current]
	scanner.current += 1
	return c
}

func (scanner *Scanner) peek() byte {
	if scanner.isAtEnd() {
		return '0'
	} else {
		return scanner.source[scanner.current]
	}
}

func (scanner *Scanner) peekNext() byte {
	if scanner.current+1 >= len(scanner.source) {
		return '0'
	} else {
		return scanner.source[scanner.current+1]
	}
}

func (scanner *Scanner) match(expected byte) bool {
	if scanner.isAtEnd() {
		return false
	} else if scanner.source[scanner.current] != expected {
		return false
	} else {
		scanner.current += 1
		return true
	}
}

func (scanner *Scanner) addToken(typ TokenType, literal interface{}) {
	text := scanner.source[scanner.start:scanner.current]
	token := NewToken(typ, text, literal, scanner.line)
	scanner.tokens = append(scanner.tokens, *token)
}

func (scanner *Scanner) scanToken() {
	c := scanner.advance()

	// Single chars
	switch c {

	case ' ':
	case '\t':
	case '\r':
	case '\n':
		scanner.line += 1
	case '(':
		scanner.addToken(LeftParen, nil)
	case ')':
		scanner.addToken(RightParen, nil)
	case '{':
		scanner.addToken(LeftBrace, nil)
	case '}':
		scanner.addToken(RightBrace, nil)
	case ',':
		scanner.addToken(Comma, nil)
	case '.':
		scanner.addToken(Dot, nil)
	case '-':
		scanner.addToken(Minus, nil)
	case '+':
		scanner.addToken(Plus, nil)
	case '*':
		scanner.addToken(Star, nil)
	// Operators
	case '!':
		if scanner.match('=') {
			scanner.addToken(BangEqual, nil)
		} else {
			scanner.addToken(Bang, nil)
		}
	case '=':
		if scanner.match('=') {
			scanner.addToken(EqualEqual, nil)
		} else {
			scanner.addToken(Equal, nil)
		}
	case '<':
		if scanner.match('=') {
			scanner.addToken(LessEqual, nil)
		} else {
			scanner.addToken(Less, nil)
		}
	case '>':
		if scanner.match('=') {
			scanner.addToken(GreaterEqual, nil)
		} else {
			scanner.addToken(Greater, nil)
		}
	// Longer ones
	case '/':
		if scanner.match('/') {
			for scanner.peek() != '\n' && !scanner.isAtEnd() {
				scanner.advance()
			}
		} else {
			scanner.addToken(Slash, nil)
		}
	// Literals
	case '\'':
		scanner.handleString()
	case '0', '1', '2', '3', '4', '5', '6', '7', '8', '9':
		scanner.handleNumber()
	default:
		if isAlpha(c) {
			scanner.handleIdentifier()
		} else {
			// Fail!
			scanner.handler.error(scanner.line, "Unexpected character: '"+string(c)+"'")
		}
	}
}

func (scanner *Scanner) handleString() {
	for scanner.peek() != '\'' && !scanner.isAtEnd() {
		if scanner.peek() == '\n' {
			scanner.line += 1
		}
		scanner.advance()
	}

	if scanner.isAtEnd() {
		scanner.handler.error(scanner.line, "Unterminated string.")
		return
	}

	// Move past the closing quote char
	scanner.advance()

	value := scanner.source[scanner.start+1 : scanner.current-1]
	scanner.addToken(String, value)
}

func (scanner *Scanner) handleNumber() {
	for isNumeric(scanner.peek()) {
		scanner.advance()
	}
	// Consume a dot, and digits after it
	hasDot := false
	if scanner.peek() == '.' && isNumeric(scanner.peekNext()) {
		hasDot = true
		scanner.advance()
		for isNumeric(scanner.peek()) {
			scanner.advance()
		}
	}

	s := scanner.source[scanner.start:scanner.current]
	if hasDot {
		value, e := strconv.ParseFloat(s, 64)
		if e != nil {
			panic("not a float")
		}
		scanner.addToken(Number, value)
	} else {
		value, e := strconv.ParseInt(s, 10, 64)
		if e != nil {
			panic("not an int")
		}
		scanner.addToken(Number, value)
	}
}

func (scanner *Scanner) handleIdentifier() {
	for isAlphaNumeric(scanner.peek()) {
		scanner.advance()
	}

	name := scanner.source[scanner.start:scanner.current]
	if stringIsKeyword(name) {
		scanner.addToken(Keyword, nil)
	} else {
		scanner.addToken(Identifier, nil)
	}
}

func isAlpha(c byte) bool {
	return 'a' <= c && c <= 'z' ||
		'A' <= c && c <= 'Z' ||
		c == '_'
}

func isNumeric(c byte) bool {
	return '0' <= c && c <= '9'
}
func isAlphaNumeric(c byte) bool {
	return isAlpha(c) || isNumeric(c)
}
