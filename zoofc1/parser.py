from .tokens import TT, Token
from . import tree


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
        self.matchEos()  # skip initial comments and newlines
        statements = self.statements()
        if not self.check(TT.EOF):
            self.error(self.peek(), "Unexpected end", throw=False)
        return statements

    def match(self, *tokentypes):
        for tokentype in tokentypes:
            if self.check(tokentype):
                self.advance()
                return True
        return False

    def matchKeyword(self, *keywords):
        token = self.peek()
        if token.type == TT.Keyword and token.lexeme in keywords:
            self.advance()
            return True
        else:
            return False

    def check(self, tokentype):
        return self.peek().type == tokentype

    def advance(self):
        token = self.peek()
        if token.type != TT.EOF:
            self.current += 1
        return token

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
        while not self.matchEos():
            self.advance()

    # %%

    def matchEos(self):
        # todo: we can drop the check for eof in many places, because its always preceded by an eol
        # End Of Statement
        self.match(TT.Comment)
        if self.check(TT.Newline):
            self.advance()
            while True:
                self.match(TT.Comment)
                if not self.check(TT.Newline):
                    break
                self.advance()
            return True
        else:
            return False

    def consumeEos(self):
        if not self.matchEos():
            self.error(self.peek(), "Expected newline")

    def statements(self):
        # Collect a list of statements
        statements = []

        while not self.match(TT.Dedent, TT.EOF):
            try:
                statements.append(self.statement())
            except ParseError:
                self.synchronize()

            # elif self.match(TT.InvalidIndentation):
            #     self.error(self.peek(), "Unexpected indent.")

        return statements

    def indentedStatements(self, context):
        self.consume(TT.Indent, "Expected indentation on line " + context)
        return self.statements()

    def statement(self):
        # -> (expressionStmt | printStmt | ... ) ((Comment)? Newline | EOF)
        if self.matchKeyword("do"):
            return tree.BlockStmt(self.blockStatement())
        elif self.matchKeyword("if"):
            return self.ifStatement()
        elif self.matchKeyword("for", "while"):
            return self.loopStatement()
        elif self.matchKeyword("break"):
            token = self.previous()
            self.consumeEos()
            return tree.BreakStmt(token)
        elif self.matchKeyword("return"):
            return self.returnStatement()
        elif self.matchKeyword("print"):
            return self.printStatement()
        elif self.matchKeyword("func"):
            return self.funcStatement("function")
        else:
            return self.expressionStatement()

    def blockStatement(self):
        # -> "do" "{" statement* "}" "\n"
        self.consume(TT.LeftBrace, "Expected '{' after 'do'.")
        self.consumeEos()
        statements = self.indentedStatements("after 'do'")
        self.consume(TT.RightBrace, "Expected '}' at the end of 'do'.")
        self.consumeEos()
        return statements

    def ifStatement(self):
        # -> "if" expression EOS statement* ("else" EOS statement*)?
        condition = self.expression()
        then = self.peek()

        if not self.matchKeyword("then"):
            self.error(self.peek(), "expect 'then' after if-condition")

        if self.matchEos():
            # Statement-mode

            thenStatements = self.indentedStatements("after 'if'")
            elseStatements = []

            if self.matchKeyword("elseif"):
                elseStatements = [self.ifStatement()]
            elif self.matchKeyword("else"):
                if self.matchKeyword("if"):
                    elseStatements = [self.ifStatement()]
                else:
                    self.consumeEos()
                    elseStatements = self.indentedStatements("after 'else'")

            return tree.IfStmt(then, condition, thenStatements, elseStatements)

        else:
            # expression mode
            thenExpression = self.expression()
            if not self.matchKeyword("else"):
                self.error(
                    self.peek(),
                    "In single-line if-expression, an else-clause is required.",
                )
            elseExpression = self.expression()
            return tree.IfStmt(then, condition, [thenExpression], [elseExpression])
            # return tree.IfExpr(then, condition, thenExpression, elseExpression)

    def loopStatement(self):
        # -> "loop" ( expression | expression "over" expression) "do" EOS statement*
        # Note: Until I make up my mind about the syntax that I want, this allows all variations of:
        # for i in xx do
        # while i in xx do
        # loop i in xx do
        # for i < x do
        # etc.
        loopOp = self.previous()
        if self.matchKeyword("do"):
            # Infinite loop (a.k.a. while-true-loop)
            trueToken = Token(TT.LiteralTrue, loopOp.lexeme, loopOp.line, loopOp.column)
            stmt = tree.WhileStmt(loopOp, tree.LiteralExpr(trueToken), [])
        else:
            expr = self.expression()
            if self.matchKeyword("in", "over"):
                # Loop iter (a.k.a. a for-loop)
                var = expr
                if not isinstance(var, tree.VariableExpr):
                    self.error(
                        self.previous(), "in 'for x in y', 'x' must be a variable"
                    )
                iterator = self.expression()
                stmt = tree.ForStmt(loopOp, var, iterator, [])
            else:
                # Loop condition (a.k.a. a while-loop)
                condition = expr
                stmt = tree.WhileStmt(loopOp, condition, [])

            if not self.matchKeyword("do"):
                self.error(self.peek(), "expect 'do' after loop condition")

        if self.matchEos():
            # Statement-mode
            statements = self.indentedStatements("after 'loop'")
            if self.matchKeyword("else"):
                self.error(self.previous(), "loop-else not (yet?) supported")
            stmt.statements = statements
            return stmt
        else:
            # Expression-mode
            expr = self.expression()
            if self.matchKeyword("else"):
                self.error(
                    self.previous(),
                    "In single-line loop-expression, the else-clause is forbidden",
                )
            stmt.statements = [expr]
            return stmt

    def funcStatement(self, kind):
        # -> "func" IDENTIFIER "(" parameters? ")" "do" EOS statement*
        # parameters -> IDENTIFIER ( "," IDENTIFIER )* ","?
        # todo: should we prohibit function/class declarations inside loops or ifs? E.g. only in the "root" of a scope?
        name = self.consume(TT.Identifier, f"Expect {kind} name")
        self.consume(TT.LeftParen, "Expect '(' after {kind} name")
        params = []
        if not self.match(TT.RightParen):
            while True:
                params.append(self.consume(TT.Identifier, "Expect parameter name"))
                if len(params) > 250:
                    self.error(self.peek(), "Cannot have more than 250 parameters.")
                hasComma = self.match(TT.Comma)
                if self.match(TT.RightParen):
                    break
                if not hasComma:
                    self.error(self.peek(), "Expecting ',' or ')' after argument.")

        if not self.matchKeyword("do"):
            self.error(self.peek(), "expect 'do' after function signature")

        if self.matchEos():
            # Statement-mode
            statements = self.indentedStatements("after 'func'")
        else:
            # Expression-mode
            statements = [self.expression()]

        return tree.FunctionStmt(name, params, statements)

    def returnStatement(self):
        # -> "return" expression? EOS
        keyword = self.previous()
        value = None
        if not self.matchEos():
            value = self.expression()
        if not self.matchEos():
            self.error(keyword, "Expected newline after return value")
        return tree.ReturnStmt(keyword, value)

    def printStatement(self):
        # -> "print" expression "\n"
        value = self.expression()
        self.consumeEos()
        return tree.PrintStmt(value)

    def expressionStatement(self):
        # -> expression "\n"
        expr = self.expression()
        self.consumeEos()
        return tree.ExpressionStmt(expr)

    # %%

    # Note: Wren lists a nice precedence table here: https://wren.io/syntax.html
    # Note: as soon as I have proper tests and benchmarks, lets try to replace this with precedense climbing https://eli.thegreenplace.net/2012/08/02/parsing-expressions-by-precedence-climbing

    def expression(self):
        # -> ifexpr
        expr = self.ifexpr()
        return expr

    def ifexpr(self):
        # -> 'if' assignment 'then' assignment 'else' assignment
        if self.matchKeyword("if"):
            condition = self.assignment()
            then = self.peek()
            if not self.matchKeyword("then"):
                self.error(self.peek(), "expect 'then' after if-condition")
            if self.matchEos():
                self.error(then, "An if-expression must be on a single line")
            thenExpression = self.assignment()
            if not self.matchKeyword("else"):
                self.error(
                    then,
                    "In single-line if-expression, an else-expression is required.",
                )
            elseExpression = self.assignment()
            return tree.IfExpr(then, condition, thenExpression, elseExpression)
        else:
            return self.assignment()

    def assignment(self):
        # -> IDENTIFIER  "=" assignment | logicalOr
        expr = self.logicalOr()
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

    def logicalOr(self):
        # -> logicalAnd "or" logicalAnd
        expr = self.logicalAnd()
        while self.matchKeyword("or"):
            operator = self.previous()
            right = self.logicalAnd()
            expr = tree.LogicalExpr(expr, operator, right)
        return expr

    def logicalAnd(self):
        # -> equality "and" equality
        expr = self.equality()
        while self.matchKeyword("and"):
            operator = self.previous()
            right = self.equality()
            expr = tree.LogicalExpr(expr, operator, right)
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
        # -> litrange ( ( "/" | "*" ) litrange )* ;
        expr = self.litrange()
        while self.match(TT.Slash, TT.Star):
            op = self.previous()
            right = self.litrange()
            expr = tree.BinaryExpr(expr, op, right)
        return expr

    def litrange(self):
        # -> power ".." power (".." power)?
        expr = self.power()
        rangeOp = self.peek()
        if self.match(TT.DotDot):
            expr2 = self.power()
            if self.match(TT.DotDot):
                expr3 = self.power()
            else:
                nilToken = Token(TT.LiteralNil, "nil", rangeOp.line, rangeOp.column)
                expr3 = tree.LiteralExpr(nilToken)
            expr = tree.RangeExpr(expr, expr2, expr3)
        return expr

    def power(self):
        # -> unary ( "^" unary )* ;
        expr = self.unary()
        if self.match(TT.Caret):
            op = self.previous()
            right = self.power()
            expr = tree.BinaryExpr(expr, op, right)
        return expr

    def unary(self):
        # -> ( "!" | "-" ) primary | call
        # todo: can I only allow unary at the start of a nuneric expression?
        if self.match(TT.Plus, TT.Minus):
            op = self.previous()
            right = self.primary()  # only allow one unary
            return tree.UnaryExpr(op, right)
        else:
            return self.call()

    def call(self):
        # -> primary ( "(" arguments? ")" )*
        # arguments -> expression ( "," expression )* ","?
        # Bit weird way to spell this, but will make sense when we add attr access
        expr = self.primary()
        while True:
            if self.match(TT.LeftParen):
                expr = self.finishCall(expr)
            else:
                break
        return expr

    def finishCall(self, callee):
        arguments = []
        if self.match(TT.RightParen):
            pass  # no args
        else:
            while True:
                arguments.append(self.expression())
                if len(arguments) > 250:
                    self.error(self.peek(), "Cannot have more than 250 arguments.")
                hasComma = self.match(TT.Comma)
                if self.match(TT.RightParen):
                    break
                if not hasComma:
                    self.error(self.peek(), "Expecting ',' or ')' after argument.")

        return tree.CallExpr(callee, self.previous(), arguments)

    def primary(self):
        # -> NUMBER | STRING | "true" | "false" | "nil" | "(" expression ")" ;
        if self.match(
            TT.LiteralFalse,
            TT.LiteralTrue,
            TT.LiteralNil,
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
