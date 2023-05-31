from .tokens import TT, Token
from . import tree


class ParseError(Exception):
    pass


class Parser:
    """A recursive descent parser."""

    def __init__(self, errorHandler):
        self.ehandler = errorHandler
        self.tokens = []
        self.current = 0

    def parse(self, source, tokens):
        """Parse a series of tokens and generate a list of statements.

        The parser can be reused to parse different pieces of code, but
        not concurrently (i.e. not thread safe).
        """
        # program -> statement* EOF

        # Init
        self.ehandler.swapSource(source)
        self.tokens = tokens
        self.current = 0

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

    def peekNext(self):
        i = self.current + 1
        if i >= len(self.tokens):
            return TT.EOF
        return self.tokens[i]

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
            return self.doStatement()
        elif self.matchKeyword("if"):
            return self.ifStatement()
        elif self.matchKeyword("for"):
            return self.forStatement()
        elif self.matchKeyword("while"):
            return self.whileStatement()
        elif self.matchKeyword("break"):  # we'll do 'continue' later
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

    def doStatement(self):
        # -> "do" EOS statement*
        if not self.matchEos():
            self.error(
                self.peek(),
                "After 'do' further statements are expected on a new (indented) line.",
            )
        statements = self.indentedStatements("after 'do'")
        return tree.DoStmt(statements)

    def ifStatement(self):
        # -> "if" expression "do" EOS statement* ("else" EOS statement*)?
        condition = self.expression()
        while isinstance(condition, tree.GroupingExpr):
            condition = condition.expr
        if isinstance(condition, tree.AssignExpr):
            self.error(
                self.peek(),
                "To avoid bugs, it's required to compare the result of an assignment here",
                throw=False,
            )

        then = self.peek()

        if not self.matchKeyword("do", "its"):
            self.error(self.peek(), "expect 'do' or 'its' after if-condition")

        if then.lexeme == "do":
            # Statement form

            if not self.matchEos():
                self.error(
                    self.peek(),
                    "After 'if ... do' further statements are expected on a new (indented) line.",
                )

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

        else:  # then.lexeme == "its":
            # Expression form
            expr = self.ifExpAfterIts(condition, then)
            self.consumeEos()
            return tree.ExpressionStmt(expr)

    def forStatement(self):
        # -> "for" expression "in" expression "do" EOS statement*
        loopOp = self.previous()

        var = self.expression()
        if not self.matchKeyword("in"):
            self.error(self.peek(), "expect 'in' after 'for ...'")

        if not isinstance(var, tree.VariableExpr):
            self.error(self.previous(), "in 'for x in y', 'x' must be a variable")

        # Turn variable into an assignment
        var = tree.AssignExpr(var.name, None)

        iterator = self.expression()
        stmt = tree.ForStmt(loopOp, var, iterator, [])

        if self.matchKeyword("do"):
            # Statement form
            if not self.matchEos():
                self.error(
                    self.peek(),
                    "After 'for ... do' further statements are expected on a new (indented) line.",
                )
            statements = self.indentedStatements("after 'for'")
            if self.matchKeyword("else"):
                self.error(self.previous(), "for-else not (yet?) supported")
            stmt.statements = statements
            return stmt

        elif self.matchKeyword("its"):
            # Expression form

            # expr = self.forExpAfterIts(condition, then)
            # self.consumeEos()
            # return tree.ExpressionStmt(expr)

            expr = self.expression()
            if self.matchKeyword("else"):
                self.error(
                    self.previous(),
                    "In single-line loop-expression, the else-clause is forbidden",
                )
            stmt.statements = [expr]
            self.consumeEos()
            return stmt
        else:
            self.error(self.peek(), "expect 'do' or 'its' after 'for ... in ... '")

    def whileStatement(self):
        # -> "for" expression "in" expression "do" EOS statement*
        loopOp = self.previous()

        condition = self.expression()
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

        if self.matchKeyword("do"):
            # Statement form
            if not self.matchEos():
                self.error(
                    self.peek(),
                    "After 'while ... do' further statements are expected on a new (indented) line.",
                )
            statements = self.indentedStatements("after 'while'")
            if self.matchKeyword("else"):
                self.error(self.previous(), "while-else not (yet?) supported")
            stmt.statements = statements
            return stmt

        elif self.matchKeyword("its"):
            # Expression form
            self.error(
                self.previous(),
                "The expression form 'while ... its' is not supported, use 'while ... do' instead",
            )
        else:
            self.error(self.peek(), "expect 'do' or 'its' after 'for ... in ... '")

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
            value = self.expression(allow_kw=True)
        if not self.matchEos():
            self.error(keyword, "Expected newline after return value")
        return tree.ReturnStmt(keyword, value)

    def printStatement(self):
        # -> "print" expression "\n"
        value = self.expression(allow_kw=True)
        self.consumeEos()
        return tree.PrintStmt(value)

    def expressionStatement(self):
        # -> expression "\n"
        expr = self.expression(is_statement=True, allow_kw=True)
        self.consumeEos()
        return tree.ExpressionStmt(expr)

    # %%

    OPINFO_MAP = {
        # Assignment
        TT.Equal: (1, "R", tree.AssignExpr),
        # Logical
        TT.LogicalOr: (2, "R", tree.LogicalExpr),
        TT.LogicalAnd: (3, "R", tree.LogicalExpr),
        # Equality
        TT.BangEqual: (4, "L", tree.BinaryExpr),
        TT.EqualEqual: (4, "L", tree.BinaryExpr),
        # Type test 'is'
        # Comparisons
        TT.Greater: (10, "L", tree.BinaryExpr),
        TT.GreaterEqual: (10, "L", tree.BinaryExpr),
        TT.Less: (10, "L", tree.BinaryExpr),
        TT.LessEqual: (10, "L", tree.BinaryExpr),
        # Range
        TT.Colon: (11, "L", tree.RangeExpr),
        # Bitwise ops, bitshifts
        # Basic math
        TT.Minus: (20, "L", tree.BinaryExpr),
        TT.Plus: (20, "L", tree.BinaryExpr),
        TT.Star: (21, "L", tree.BinaryExpr),
        TT.Slash: (21, "L", tree.BinaryExpr),
        TT.Caret: (22, "R", tree.BinaryExpr),
        # Unary, and the rest are handled with recursive descent in expressionUnit
    }

    def expression(self, min_prec=0, *, is_statement=False, allow_kw=False):
        # Read tokens to produce an expression.
        # This implements precedense climbing,
        # see e.g. https://eli.thegreenplace.net/2012/08/02/parsing-expressions-by-precedence-climbing
        # In this method we handle all binary operators.

        leftExpr = self.expressionUnit(allow_kw=allow_kw)

        while True:
            # Detect token for binary op
            token = self.peek()
            if token.type not in self.OPINFO_MAP:
                break
            prec, assoc, TreeCls = self.OPINFO_MAP[token.type]
            if prec < min_prec:
                break
            self.advance()  # ok, accept it!

            # Recurse. This here is the magic part of precedence climbing.
            rightExpr = self.expression(
                prec + 1 if assoc == "L" else prec,
                allow_kw=allow_kw and token.type == TT.Equal,
            )

            # Update left with the new value
            if TreeCls is tree.AssignExpr:
                leftExpr = self.handleAssign(leftExpr, token, rightExpr, is_statement)
            elif TreeCls is tree.RangeExpr:
                if isinstance(leftExpr, tree.RangeExpr):
                    if leftExpr.step is not None:
                        self.error(
                            token,
                            "Cannot stack colon operators more than twice",
                            throw=False,
                        )
                    leftExpr = tree.RangeExpr(leftExpr.start, leftExpr.stop, rightExpr)
                else:
                    leftExpr = tree.RangeExpr(leftExpr, rightExpr, None)
            else:
                leftExpr = TreeCls(leftExpr, token, rightExpr)

        return leftExpr

    def expressionUnit(self, *, allow_kw=False):
        # An expression that can be of either side of a binary expression.
        # We enter recursive descent mode again, although we've grouped some things
        # to make it easier to read.

        # Stuff in front - unary operators
        if self.match(TT.Plus, TT.Minus):
            op = self.previous()
            right = self.expressionUnit()
            if isinstance(right, tree.UnaryExpr):
                self.error(right.op, "Unaries do not stack")
            expr = tree.UnaryExpr(op, right)
        else:
            expr = self.expressionWithKeyword(allow_kw=allow_kw)

        # Stuff behind - calls, subscript, attributes
        while True:
            if self.match(TT.LeftParen):
                expr = self.finishCall(expr)
            else:
                break

        return expr

    def expressionWithKeyword(self, *, allow_kw=False):
        if self.match(TT.Keyword):
            lexeme = self.previous().lexeme
            if not allow_kw:
                self.error(
                    self.previous(),
                    f"{lexeme}-expression not allowed here, try wrapping it in parentheses: `(...)`",
                )
            elif lexeme == "if":
                return self.ifExpr()
            elif lexeme == "for":
                self.error(self.previous(), "For-expressions will be implemened later.")
            elif lexeme == "func":
                return self.funcExpr()
            else:
                self.error(self.previous(), "Unexpected keyword in expression.")
        return self.primaryExpression()

    def primaryExpression(self):
        if self.match(TT.LeftParen):
            expr = self.expression(allow_kw=True)
            self.consume(TT.RightParen, "Expect ')' after expression.")
            return tree.GroupingExpr(expr)
        elif self.match(
            TT.LiteralFalse,
            TT.LiteralTrue,
            TT.LiteralNil,
            TT.LiteralNumber,
            TT.LiteralString,
        ):
            return tree.LiteralExpr(self.previous())
        elif self.match(TT.Identifier):
            return tree.VariableExpr(self.previous())
        else:
            self.error(self.peek(), "Expected expression.")

    def handleAssign(self, leftExpr, equalsToken, rightExpr, is_statement):
        if not is_statement and isinstance(rightExpr, tree.AssignExpr):
            self.error(
                equalsToken,
                "Can only stack assignments in assignment statements (not in expressions).",
                throw=False,
            )
        # Handle the assignment target
        if isinstance(leftExpr, tree.VariableExpr):
            # Convert r-value expr into l-value assignment
            name = leftExpr.name
            return tree.AssignExpr(name, rightExpr)
        else:
            # Error, but no need to unwind, because we're not in a confused state
            self.error(equalsToken, "Invalid assignment target.", throw=False)
            return leftExpr

    def finishCall(self, callee):
        arguments = []
        if self.match(TT.RightParen):
            pass  # no args
        else:
            while True:
                arguments.append(self.expression(allow_kw=True))
                if len(arguments) > 250:
                    self.error(self.peek(), "Cannot have more than 250 arguments.")
                hasComma = self.match(TT.Comma)
                if self.match(TT.RightParen):
                    break
                if not hasComma:
                    self.error(self.peek(), "Expecting ',' or ')' after argument.")

        return tree.CallExpr(callee, self.previous(), arguments)

    def ifExpr(self):
        # -> 'if' assignment 'its' assignment 'else' assignment
        condition = self.expression()
        if isinstance(condition, tree.AssignExpr):
            self.error(
                self.peek(),
                "To avoid bugs, it's required to compare the result of an assignment here",
                throw=False,
            )
        then = self.peek()
        if not self.matchKeyword("its"):
            self.error(self.peek(), "expecting 'its' after if-expression-condition")
        return self.ifExpAfterIts(condition, then)

    def ifExpAfterIts(self, condition, then):
        if self.matchEos():
            self.error(then, "An if-expression must be on a single line")
        thenExpression = self.expression()
        if not self.matchKeyword("else"):
            self.error(
                then,
                "In single-line if-expression, an else-expression is required.",
            )
        elseExpression = self.expression()
        return tree.IfExpr(then, condition, thenExpression, elseExpression)

    def funcExpr(self):
        # -> 'func' assignment
        self.consume(TT.LeftParen, "Expect '(' after ananymous 'func'")
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

        if not self.matchKeyword("its"):
            self.error(
                self.peek(), "expect 'its' after signature of anonynous function"
            )
        if self.matchEos():
            self.error(self.peek(), "a function expression must be on a single line")
        body = self.expression()

        name = ""  # in theory we could allow lambdas to have a name
        return tree.FunctionExpr(name, params, body)
