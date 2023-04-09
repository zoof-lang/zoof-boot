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
        self.refIndent = 0
        self.curIndent = 0

    def parse(self):
        # program -> statement* EOF
        statements = self.statements()
        if not self.check(TT.EOF):
            self.error(self.peek(), "Unexpected end")
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
        # Expect a certain tokentype
        if self.check(tokentype):
            return self.advance()
        else:
            self.error(self.peek(), message)

    def error(self, token, message, *, throw=True):
        self.ehandler.syntaxError(token, message)
        if throw:
            raise ParseError()  # to unwind the stack

    def synchronize(self):
        while not self.match(TT.Newline, TT.EOF):
            self.advance()

    # %%

    def skipEmptyLines(self):
        self.match(TT.Comment)
        while self.check(TT.Newline):
            self.curIndent = len(self.peek().lexeme) - 1
            self.advance()
            self.match(TT.Comment)

    def checkEos(self):
        # End Of Statement
        self.match(TT.Comment)
        if self.check(TT.Newline):
            self.curIndent = len(self.peek().lexeme) - 1
            self.advance()
        elif self.check(TT.EOF):
            self.advance()
        else:
            self.error(self.peek(), "Expected newline")

    def statements(self):
        # Collect a list of statements

        statements = []

        while True:
            # Skip whitespace
            self.skipEmptyLines()
            if self.isAtEnd():
                break
            # Check indentation
            if self.curIndent != self.refIndent:
                if self.curIndent < self.refIndent:
                    break
                else:
                    self.error(self.peek(), "Unexpected indent.")
            try:
                # Process statement
                statements.append(self.statement())
            except ParseError:
                self.synchronize()

        return statements

    def indentedStatements(self, context):
        # Collect a list of indented statements

        self.skipEmptyLines()
        if self.curIndent <= self.refIndent:
            self.error(self.peek(), "Expected indentation on line " + context)

        previousIndent = self.refIndent
        self.refIndent = self.curIndent

        statements = self.statements()

        if self.curIndent > previousIndent:
            self.error(self.peek(), "Unexpected indentation")

        self.refIndent = previousIndent
        return statements

    def statement(self):
        # -> (expressionStmt | printStmt | block) ((Comment)? Newline | EOF)
        if self.matchKeyword("do"):
            return tree.BlockStmt(self.blockStatement())
        elif self.matchKeyword("if"):
            return self.ifStatement()
        elif self.matchKeyword("print"):
            return self.printStatement()
        else:
            return self.expressionStatement()

    def blockStatement(self):
        # -> "do" "{" statement* "}" "\n"
        self.consume(TT.LeftBrace, "Expected '{' after 'do'.")
        self.checkEos()

        statements = self.indentedStatements("after 'do'")

        self.consume(TT.RightBrace, "Expected '}' at the end of 'do'.")
        if self.curIndent != self.refIndent:
            self.error(self.peek(), "Expect '}' to match the indentation level of 'do'")

        return statements

    def ifStatement(self):
        # -> "if" expression EOS statement* ("else" EOS statement*)?
        condition = self.expression()
        self.checkEos()

        thenStatements = self.indentedStatements("after 'if'")

        if self.curIndent == self.refIndent and self.matchKeyword("else"):
            self.checkEos()
            elseStatements = self.indentedStatements("after 'else'")
        else:
            elseStatements = []  # else

        return tree.IfStmt(condition, thenStatements, elseStatements)

    def printStatement(self):
        # -> "print" expression "\n"
        value = self.expression()
        self.checkEos()
        return tree.PrintStmt(value)

    def expressionStatement(self):
        # -> expression "\n"
        expr = self.expression()
        self.checkEos()
        return tree.ExpressionStmt(expr)

    # %%

    def expression(self):
        # -> assignment
        expr = self.assignment()
        return expr

    def assignment(self):
        # -> IDENTIFIER  "=" assignment | equality
        expr = self.equality()
        if self.match(TT.Equal):
            equalsToken = self.previous()
            value = self.assignment()
            if isinstance(expr, tree.VariableExpr):
                # Convert r-value expr into l-value assignment
                name = expr.name
                return tree.AssignExpr(name, value)
            else:
                # Error, but no need to unwind, because we're not in a confused state
                self.error(equalsToken, "Invalid assignment target.", throw=False)
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
        elif self.match(TT.Identifier):
            return tree.VariableExpr(self.previous())
        elif self.match(TT.LeftParen):
            expr = self.expression()
            self.consume(TT.RightParen, "Expect ')' after expression.")
            return tree.GroupingExpr(expr)
        else:
            self.error(self.peek(), "Expected expression.")
