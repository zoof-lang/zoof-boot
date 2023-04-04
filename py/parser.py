from tokens import TT
import tree


class ParseError(Exception):
    pass


class Parser:
    """A recursive descent parser."""

    def __init__(self, tokens, errorHandler):
        self.ehandler = errorHandler
        self.tokens = tokens
        self.current = 0

    def parse(self):
        # program -> statement* EOF
        statements = []
        while not self.isAtEnd():
            statements.append(self.statement())
        return statements

    def match(self, *tokentypes):
        for tokentype in tokentypes:
            if self.check(tokentype):
                self.advance()
                return True
        return False

    def matchKeyword(self, keyword):
        if self.isAtEnd():
            return False
        token = self.peek()
        if token.type == TT.Keyword and token.lexeme == keyword:
            self.advance()
            return True
        else:
            return False

    def check(self, tokentype):
        if self.isAtEnd():
            return False
        return self.peek().type == tokentype

    def advance(self):
        if not self.isAtEnd():
            self.current += 1
        return self.previous()

    def isAtEnd(self):
        return self.peek().type == TT.EOF
        # return self.current >= len(self.tokens)

    def peek(self):
        return self.tokens[self.current]

    def previous(self):
        return self.tokens[self.current - 1]

    def consume(self, tokentype, message):
        if self.check(tokentype):
            return self.advance()
        else:
            self.error(self.peek(), message)

    def error(self, token, message):
        self.ehandler.syntaxError(token, message)
        raise ParseError()  # to unwind the stack

    def synchronize(self):
        raise NotImplementedError()

    # %%

    def statement(self):
        # -> expressionStmt | printStmt
        if self.matchKeyword("print"):
            return self.printStatement()
        else:
            return self.expressionStatement()

    def printStatement(self):
        # -> "print" expression "\n"
        value = self.expression()
        # todo: expect eol?
        return tree.PrintStmt(value)

    def expressionStatement(self):
        # -> expression "\n"
        expr = self.expression()
        # todo: expect eol?
        return tree.ExpressionStmt(expr)

    # %%

    def expression(self):
        # -> equality
        expr = self.equality()
        return expr

    def equality(self):
        # -> comparison ( ( "==" | "!=" ) comparison )*
        expr = self.comparison()
        while self.match(TT.BangEqual, TT.EqualEqual):
            op = self.previous()
            right = self.comparison()
            expr = tree.BinaryExpr(expr, op, right)
        return expr

    def comparison(self):
        # -> sum ( ( "<" | "<=" | ">" | ">=") sum )*
        expr = self.sum()
        while self.match(TT.Greater, TT.GreaterEqual, TT.Less, TT.LessEqual):
            op = self.previous()
            right = self.sum()
            expr = tree.BinaryExpr(expr, op, right)
        return expr

    def sum(self):
        # aka term
        # -> product ( ( "-" | "+" ) product )* ;
        expr = self.product()
        while self.match(TT.Minus, TT.Plus):
            op = self.previous()
            right = self.product()
            expr = tree.BinaryExpr(expr, op, right)
        return expr

    def product(self):
        # aka factor
        # -> power ( ( "/" | "*" ) power )* ;
        expr = self.power()
        while self.match(TT.Slash, TT.Star):
            op = self.previous()
            right = self.power()
            expr = tree.BinaryExpr(expr, op, right)
        return expr

    def power(self):
        # -> unary ( "^" unary )* ;
        expr = self.unary()
        while self.match(TT.Caret):
            op = self.previous()
            right = self.unary()
            expr = tree.BinaryExpr(expr, op, right)
        return expr

    def unary(self):
        # -> ( "!" | "-" ) unary | primary
        # todo: can I only allow unary at the start of a nuneric expression?
        if self.match(TT.Plus, TT.Minus):
            op = self.previous()
            # right = self.unary()
            right = self.primary()  # only allow one unary
            return tree.UnaryExpr(op, right)
        else:
            return self.primary()

    def primary(self):
        # -> NUMBER | STRING | "true" | "false" | "nil" | "(" expression ")" ;
        if self.match(
            TT.LiteralFalse,
            TT.LiteralTrue,
            TT.LiteralNul,
            TT.LiteralNumber,
            TT.LiteralString,
        ):
            # return tree.LiteralExpr(self.peek())
            return tree.LiteralExpr(self.previous())
        elif self.match(TT.LeftParen):
            expr = self.expression()
            self.consume(TT.RightParen, "Expect ')' after expression.")
            return tree.GroupingExpr(expr)
        else:
            self.error(self.peek(), "Expected expression.")
