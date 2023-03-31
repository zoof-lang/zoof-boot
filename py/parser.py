from tokens import TT
import tree


class ParseError(Exception):
    pass


class Parser:
    """A recursive descent parser."""

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
        # -> equality
        expr = self.equality()
        self.advance()
        if not self.isAtEnd():
            raise self.error(self.peek(), "Unexpected expression?")
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
        if self.match(TT.Plus, TT.Minus):
            op = self.previous()
            right = self.unary()
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
            raise self.error(self.peek(), "Expected expression.")
