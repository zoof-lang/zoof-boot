from lexer import TT
import tree


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens, handler):
        self.handler = handler
        self.tokens = tokens
        self.current = 0

    def parse(self):
        try:
            return self.expression()
        except ParseError:
            return None

    def match(self, *tokentypes):
        for tokentype in tokentypes:
            if self.check(tokentype):
                self.advance()
                return True
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
        # return self.peek == TT.EOF
        return self.current >= len(self.tokens)

    def peek(self):
        return self.tokens[self.current]

    def previous(self):
        return self.tokens[self.current - 1]

    def consume(self, tokentype, message):
        if self.check(tokentype):
            return self.advance()
        else:
            raise self.error(self.peek(), message)

    def error(self, token, message):
        self.handler.error_for_token(token, message)
        return ParseError()

    def synchronize(self):
        raise NotImplementedError()

    # %%

    def expression(self):
        return self.equality()

    def equality(self):
        expr = self.comparison()
        while self.match(TT.BangEqual, TT.EqualEqual):
            op = self.previous()
            right = self.comparison()
            expr = tree.BinaryExpr(expr, op, right)
        return expr

    def comparison(self):
        expr = self.term()
        while self.match(TT.Greater, TT.GreaterEqual, TT.Less, TT.LessEqual):
            op = self.previous()
            right = self.term()
            expr = tree.BinaryExpr(expr, op, right)
        return expr

    def term(self):
        expr = self.factor()
        while self.match(TT.Minus, TT.Plus):
            op = self.previous()
            right = self.factor()
            expr = tree.BinaryExpr(expr, op, right)
        return expr

    def factor(self):
        expr = self.unary()
        while self.match(TT.Slash, TT.Star):
            op = self.previous()
            right = self.unary()
            expr = tree.BinaryExpr(expr, op, right)
        return expr

    def unary(self):
        if self.match(TT.Plus, TT.Minus):
            op = self.previous()
            right = self.unary()
            return tree.UnaryExpr(op, right)
        else:
            return self.primary()

    def primary(self):
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
            raise self.error(self.peek(), "Expected expression.")
