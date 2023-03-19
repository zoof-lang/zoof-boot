//
//  scanner.swift
//  zoof
//
//  Created by Almar Klein on 15/03/2023.
//

import Foundation

enum TokenType {
    case LeftParen, RightParen
    case LeftBrace, RightBrace
    case Comma
    case Dot
    case Minus
    case Plus
    case Semicolon
    case Slash
    case Star

    // one or two-character tokens
    case Bang, BangEqual
    case Equal, EqualEqual
    case Greater, GreaterEqual
    case Less, LessEqual

    // Literals
    case Identifier, Keyword, String, Number

    // Keywords
    case And
    case Class
    case Else
    case False
    case Fun
    case For
    case If
    case Nil
    case Or
    case Print
    case Return
    case Super
    case This
    case True
    case Var
    case While

    case EOF
}

let KEYWORDS: [String] = ["and", "import", "or", "and", "fun"]

class Token: CustomStringConvertible {
    var typ: TokenType
    var lexeme: String
    var literal: Any
    var line: Int
    
    init(_ typ: TokenType, lexeme: String, line: Int) {
        self.typ = typ
        self.lexeme = lexeme
        self.line = line
        self.literal = false
    }
    init(_ typ: TokenType, lexeme: String, line: Int, literal: Any) {
        self.typ = typ
        self.lexeme = lexeme
        self.line = line
        self.literal = literal
    }
    
    var description: String {
        if type(of: literal) != Bool.self {
            return "Token \(self.typ) '\(self.lexeme)' on line \(self.line) = \(self.literal)"
        } else {
            return "Token \(self.typ) '\(self.lexeme)' on line \(self.line)"
        }
      }
}

// Either the CustomStringConvertible protocol + description computed var, or a custom string init
//extension String {
//  init(_ token: Token) {
//      self = "Token \(token.typ) \(token.lexeme) on line \(token.line)"
//  }
//}



public class Scanner {
    var source: String
    var handler: ErrorHandler
    var tokens: [Token] = []
    var line: Int
    
    var start: Int
    var current: Int
    
    init(_ source: String, _ handler: ErrorHandler) {
        self.source = source
        self.handler = handler
        self.tokens = []
        self.line = 1
        self.start = 0
        self.current = 0
    }
    
    func scanTokens() -> [Token] {
        while !isAtEnd() {
            self.start = self.current
            self.scanToken()
        }
        tokens.append(Token(.EOF, lexeme:"", line: line))
        return tokens
    }
    
    func isAtEnd() -> Bool {
        return self.current >= self.source.count
    }
    
    func advance() -> Character {
        let c = source[source.index(source.startIndex, offsetBy:current)]
        self.current += 1
        return c
    }
    
    func peek() -> Character {
        if isAtEnd() {
            return "\0"
        } else {
            return source[source.index(source.startIndex, offsetBy:current)]
        }
    }
    
    func peekNext() -> Character {
        if self.current + 1 >= self.source.count {
            return "\0"
        } else {
            return source[source.index(source.startIndex, offsetBy:(current + 1))]
        }
    }
    
    func match(_ expected: Character) -> Bool {
        if isAtEnd() {
            return false
        } else {
            let c = source[source.index(source.startIndex, offsetBy:current)]
            if c != expected {
                return false
            } else {
                self.current += 1
                return true
            }
        }
    }
    
    func addToken(_ type: TokenType) {
        let i1 = source.index(source.startIndex, offsetBy:start)
        let i2 = source.index(source.startIndex, offsetBy:current-1)
        let lexeme = String(source[i1 ... i2])
        let token = Token(type, lexeme: lexeme, line: line)
        self.tokens.append(token)
    }
    func addToken(_ type: TokenType, _ literal: String) {
        let i1 = source.index(source.startIndex, offsetBy:start)
        let i2 = source.index(source.startIndex, offsetBy:current-1)
        let lexeme = String(source[i1 ... i2])
        let token = Token(type, lexeme: lexeme, line: line, literal: literal)
        self.tokens.append(token)
    }
    func addToken(_ type: TokenType, _ literal: Int) {
        let i1 = source.index(source.startIndex, offsetBy:start)
        let i2 = source.index(source.startIndex, offsetBy:current-1)
        let lexeme = String(source[i1 ... i2])
        let token = Token(type, lexeme: lexeme, line: line, literal: literal)
        self.tokens.append(token)
    }
    func addToken(_ type: TokenType, _ literal: Double) {
        let i1 = source.index(source.startIndex, offsetBy:start)
        let i2 = source.index(source.startIndex, offsetBy:current-1)
        let lexeme = String(source[i1 ... i2])
        let token = Token(type, lexeme: lexeme, line: line, literal: literal)
        self.tokens.append(token)
    }
    
    func scanToken() {
        let c = advance()
        
        // Single chars
        switch c {
        case "(": addToken(.LeftParen)
        case ")": addToken(.RightParen)
        case "{": addToken(.LeftBrace)
        case "}": addToken(.RightBrace)
        case ",": addToken(.Comma)
        case ".": addToken(.Dot)
        case "-": addToken(.Minus)
        case "+": addToken(.Plus)
        case "*": addToken(.Star)
            // Operators
        case "!":
            addToken(match("=") ? .BangEqual : .Bang)
        case "=":
            addToken(match("=") ? .EqualEqual : .Equal)
        case "<":
            addToken(match("=") ? .LessEqual : .Less)
        case ">":
            addToken(match("=") ? .GreaterEqual : .Greater)
            // Longer ones
        case "/":
            if match("/") {
                while peek() != "\n" && !isAtEnd() {
                    _ = advance()
                }
            } else {
                addToken(.Slash)
            }
        case " ", "\t", "\r": break // whitespace
        case "\n":
            self.line += 1
        // Literals
        case "'":
            handleString()
        default:
            if isNumeric(c) {
                handleNumber()
            } else if isAlpha(c) {
                handleIdentifier()
            } else {
                handler.error(line, "Unexpected character.")
            }
        }
    }
    
    func handleString() {
        while peek() != "'" && !self.isAtEnd() {
            if peek() == "\n" {
                self.line += 1
            }
            _ = self.advance()
        }
        if isAtEnd() {
            handler.error(line, "Unterminated string.")
            return
        }
                
        // Move past the closing quote char
        _ = advance()
        
        let i1 = source.index(source.startIndex, offsetBy:(start+1))
        let i2 = source.index(source.startIndex, offsetBy:(current-2))
        let value = String(source[i1 ... i2])
        addToken(.String, value)
    }
                              
    func handleNumber() {
        while isNumeric(peek()) {
            _ = self.advance()
        }
        // Consume a dot, and digits after it
        var hasDot = false
        if self.peek() == "." && isNumeric(peekNext()) {
            hasDot = true
            _ = advance()
            while isNumeric(peek()) {
                _ = advance()
            }
        }
        
        let i1 = source.index(source.startIndex, offsetBy:start)
        let i2 = source.index(source.startIndex, offsetBy:current-1)
        let s = String(source[i1 ... i2])
        
        if hasDot {
            //self.addToken(.Number)
            self.addToken(.Number, Double(s)!)
        } else {
            //self.addToken(.Number)
            self.addToken(.Number, Int(s)!)
        }
    }
    
    func handleIdentifier() {
        while isAlphaNumeric(peek()) {
            _ = advance()
        }
        
        let i1 = source.index(source.startIndex, offsetBy:start)
        let i2 = source.index(source.startIndex, offsetBy:current)
        let name = String(source[i1 ... i2])
        
        if KEYWORDS.contains(name) {
            addToken(.Keyword)
        } else {
            addToken(.Identifier)
        }
    }
}

func isNumeric(_ c: Character) -> Bool {
    return c.isNumber
}

func isAlpha(_ c: Character) -> Bool {
    return c.isLetter || c == "_"
}

func isAlphaNumeric(_ c: Character) -> Bool {
    return c.isNumber || c == "_" ||  c.isLetter
}
