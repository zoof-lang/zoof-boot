from .tokens import TT, Token
from . import tree


class ParseError(Exception):
    pass


HINT_IF = """
The syntax for 'if' has two forms. The (multi-line) statement form, e.g.:

    if a == 42 do
        b = true
        print 'yes!'
    else
       print 'no'


And the (single-line) expression form, e.g.:

    print if a == 42 its 'yes!' else 'no'
"""

HINT_FOR = """
For-loops in Zoof always iterate a variable over a sequence.

The syntax for 'for' has two forms. The (multi-line) statement form, e.g.:

    for i in 0:10 do
        print i

And the (single-line) expression form, e.g.:

    # Note that this form is still a work in progress
    print for i in 0:10 its i
"""

HINT_WHILE = """
The syntax for 'while' loops is similar to other languages, e.g.:

    i = 0
    while i < 10 do
        i = i + 1
        print i

There is *no* (single-line) expression form for while loops.
"""

HINT_FUNC = """
The syntax for creating functions has two forms. The (multi-line) statement form, e.g.:

    func foo() do
        print 'hello!'

And the (single-line) expression form, e.g.:

    foo = func() its 'hello!'
"""


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
            self.error(
                "E1361",
                "Parsing ended before EOF (end of file).",
                self.peek(),
                "Unexpected code after parsing was finished. This is an internal parser error that should not occur in practice.",
                throw=False,
            )

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

    def error(self, errorCode, token, message, *explanation, throw=True, **kwargs):
        explanation = "\n".join(explanation)
        self.ehandler.syntaxError(errorCode, token, message, explanation, **kwargs)
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

    def consumeEosAfterKeyword(self):
        if not self.matchEos():
            kw = self.previous().lexeme
            token = self.peek()
            self.error(
                "E1087",
                f"Unexpected code after '{kw}'.",
                token,
                f"No code is allowed after the {kw} keyword.",
                f"Perhaps you meant to write this on a new line?",
            )

    def consumeEosAfterExpression(self):
        if not self.matchEos():
            token = self.peek()
            self.error(
                "E1027",
                f"Unexpected code after expression.",
                token,
                f"It is unclear how '{token.lexeme}' relates to the expression before it.",
                f"Perhaps you meant to add an operator, or put it on a new line?",
            )

    def indentedStatements(self, context, couldAlsoHaveUsedIts):
        # An indented block. This follows on:
        # - a do keyword
        # - an else keyword
        #

        token = self.previous()

        if not self.matchEos():
            line = self.ehandler.getLineOfToken(self.peek()).strip()

            pieces = line.split(token.lexeme)
            example1 = "\n".join(
                "    " * i + (piece.strip() + " " + token.lexeme).strip()
                for i, piece in enumerate(pieces, 1)
            )
            example1 = example1[: -len(token.lexeme) - 1]
            explanation = f"After '{context}', further statements are expected on a new indented line.\n"
            explanation += "Perhaps you meant:\n\n" + example1
            if couldAlsoHaveUsedIts:
                explanation += "\n\nOr perhaps you intended to use the expression form using 'its'."
            self.error(
                "E1829",
                f"Unexpected code after '{context}'.",
                self.peek(),
                explanation,
            )

        if not self.match(TT.Indent):
            self.error(
                "E1515",
                f"Expected an indented block after '{context}'",
                self.peek(),
                f"The code-block after a 'do' or 'else' keyword must be indented, so that",
                f"both the compiler and human readers can follow the structure of the code.",
                f"",
                f"If this code was meant to be in the body of the {context} block, you should indent it.",
                "If you don't want the body to do anything, add an indented line that just says 'nil'.",
                linesBefore=1,
            )
        return self.statements()

    def statements(self):
        # Collect a list of statements
        statements = []

        while True:
            if self.match(TT.Dedent, TT.EOF):
                break
            elif self.match(TT.InvalidIndentation):
                self.error(
                    "E1616",
                    "Unindent does not match any outer indentation level.",
                    self.peek(),
                    "The indentation level does not match that of the previous lines.",
                    linesBefore=2,
                    throw=False,
                )

            try:
                statements.append(self.statement())
            except ParseError:
                self.synchronize()

        return statements

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
            self.consumeEosAfterKeyword()
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
        return tree.DoStmt(self.indentedStatements("do", False))

    def ifStatement(self):
        # -> "if" expression "do" EOS statement* ("else" EOS statement*)?
        ifToken = self.previous()

        condition = self.expression()
        while isinstance(condition, tree.GroupingExpr):
            condition = condition.expr
        if isinstance(condition, tree.AssignExpr):
            self.error(
                "E1366",
                "Bare assignment not allowed here.",
                condition,
                "To avoid the bug that '=' is used when '==' was intended,",
                f"it's required to compare the result of an assignment here.",
                throw=False,
            )

        if self.matchKeyword("do"):
            # Statement form

            thenStatements = self.indentedStatements("if-do", True)
            elseStatements = []

            if self.matchKeyword("elseif"):
                elseStatements = [self.ifStatement()]
            elif self.matchKeyword("else"):
                if self.matchKeyword("if"):
                    elseStatements = [self.ifStatement()]
                else:
                    elseStatements = self.indentedStatements("if-else", False)

            return tree.IfStmt(ifToken, condition, thenStatements, elseStatements)

        elif self.matchKeyword("its"):
            # Expression form
            expr = self.ifExpAfterIts(ifToken, condition, couldBeStatement=True)
            self.consumeEosAfterExpression()
            return tree.ExpressionStmt(expr)
        else:
            self.error(
                "E1558",
                "Expected 'do' or 'its' after if-condition.",
                self.peek(),
                HINT_IF,
            )

    def forStatement(self):
        # -> "for" expression "in" expression "do" EOS statement*
        kwToken = self.previous()

        # Get variable. If no expression is found, an error is shown that explains the for syntax.
        var = self.expression()

        # Turn the expression into an assignment expression.
        if not isinstance(var, tree.VariableExpr):
            self.error(
                "E1802",
                "Expected the loop iterable to be a variable.",
                var,
                "In 'for x in y', 'x' must be a variable.",
            )
        var = tree.AssignExpr(var.name, None)

        # The in-keywords separates iter and iterable
        if not self.matchKeyword("in"):
            self.error(
                "E1208",
                "Expected 'in' after the loop iterable.",
                self.peek(),
                HINT_FOR,
            )

        # Another expression, we try to cover common mistakes in primaryExpression().
        iterator = self.expression()

        # Prepare the statement
        stmt = tree.ForStmt(kwToken, var, iterator, [])

        if not self.matchKeyword("do", "its"):
            self.error(
                "E1436",
                "Expected 'do' or 'its' to define a for-loop.",
                self.peek(),
                HINT_FOR,
            )
        doToken = self.previous()

        if doToken.lexeme == "do":
            # Statement form
            statements = self.indentedStatements("for-do", False)
            if self.matchKeyword("else"):
                self.error(
                    "E1259",
                    "for-else not (yet?) supported",
                    self.previous(),
                    throw=False,
                )
                _ = self.indentedStatements("for-else", False)

            stmt.statements = statements
            return stmt

        else:
            # Expression form

            # We can later replace this with something like this:
            # expr = self.forExpAfterIts(condition, then)
            # self.consumeEosAfterExpression()
            # return tree.ExpressionStmt(expr)

            expr = self.expression()
            if self.matchKeyword("else"):
                self.error(
                    "E1788",
                    "In single-line for-expressions, the else-clause is forbidden.",
                    self.previous(),
                )
            stmt.statements = [expr]
            self.consumeEosAfterExpression()
            return stmt

    def whileStatement(self):
        # -> "for" expression "in" expression "do" EOS statement*
        kwToken = self.previous()

        # Get condition. If no expression is found, an error is shown that explains the while syntax.
        condition = self.expression()

        if not self.matchKeyword("do"):
            self.error(
                "E1901",
                "Expected 'do' to define a while-loop.",
                self.peek(),
                "Also, the while-loop does not support an expression form using 'its'.",
            )

        statements = self.indentedStatements("while-do", False)
        return tree.WhileStmt(kwToken, condition, statements)

    def funcStatement(self, kind):
        # -> "func" IDENTIFIER "(" parameters? ")" "do" EOS statement*
        # parameters -> IDENTIFIER ( "," IDENTIFIER )* ","?
        # todo: should we prohibit function/class declarations inside loops or ifs? E.g. only in the "root" of a scope?
        funcToken = self.previous()

        if self.match(TT.Identifier):
            name = self.previous()
        else:
            name = None

        if not self.match(TT.LeftParen):
            self.error(
                "E1286",
                f"Expected '(' to start {kind} signature.",
                self.peek(),
                HINT_FUNC,
            )

        params = self.funcParameters()

        if self.matchKeyword("do"):
            # Statement-mode
            if name is None:
                self.error(
                    "E1959",
                    f"Expected {kind} name",
                    self.peek(),
                    HINT_FUNC,
                )
            statements = self.indentedStatements("func-do", True)
        elif self.matchKeyword("its"):
            # Expression-mode
            body = self.expression()
            self.consumeEosAfterExpression()
            name = name or ""
            expr = tree.FunctionExpr(funcToken, name, params, body)
            return tree.ExpressionStmt(expr)
        else:
            self.error(
                "E1653",
                "Expected 'do' or 'its' after function signature.",
                self.peek(),
            )

        return tree.FunctionStmt(name, params, statements)

    def returnStatement(self):
        # -> "return" expression? EOS
        keyword = self.previous()
        value = None
        has_value = False
        if not self.matchEos():
            value = self.expression(allow_kw=True)
            has_value = True
        if not self.matchEos():
            after = "return value" if has_value else "return"
            self.error(
                "E1536",
                "Unexpected code after {after}.",
                keyword,
                "The return keyword can be followed by 0 or 1 expressions.",
            )
        return tree.ReturnStmt(keyword, value)

    def printStatement(self):
        # -> "print" expression "\n"
        value = self.expression(allow_kw=True)
        self.consumeEosAfterExpression()
        return tree.PrintStmt(value)

    def expressionStatement(self):
        # -> expression "\n"
        expr = self.expression(is_statement=True, allow_kw=True)
        self.consumeEosAfterExpression()
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
                            "E1951",
                            "Cannot use colon operators more than twice in a row.",
                            leftExpr,
                            "A range can be created with e.g. `0:9`. Add a step with e.g. `0:9:2`",
                            "but adding more `:` operators does not make sense.",
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
                self.error(
                    "E1035",
                    "Unaries do not stack.",
                    right,
                    "You can do '-4', but not '--4'.",
                )
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
            result = None
            if lexeme == "if":
                result = self.ifExpr()
            elif lexeme == "func":
                result = self.funcExpr(self.previous())
            elif lexeme == "for":
                self.error(
                    "E1614",
                    "For-expressions will be implemened later.",
                    self.previous(),
                )
            else:
                hint = f"An expression was expected, but found '{lexeme}'."
                if lexeme == "do":
                    hint += "\nPerhaps part of the statement before 'do' is missing?"
                self.error(
                    "E1125",
                    "Unexpected keyword in expression.",
                    self.previous(),
                    hint,
                )
            # Only produce result if keywords were actually allowed
            if not allow_kw:
                self.error(
                    "E1321",
                    f"This {lexeme}-expression is not allowed here.",
                    result,
                    f"To keep code readable, you must wrap it in parentheses: `(...)`.",
                )
            return result
        return self.primaryExpression()

    def primaryExpression(self):
        if self.match(TT.LeftParen):
            expr = self.expression(allow_kw=True)
            if not self.match(TT.RightParen):
                self.error(
                    "E1895",
                    "Expect ')' after expression.",
                    self.peek(),
                    "The matching closing brace could not be found.",
                )
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
            self.primaryExpressionError()

    def primaryExpressionError(self):
        # When we expect an expression but got something else, this
        # could be for several reasons, this code tries to detect what's
        # wrong, so we can give a better error message.
        prev = self.previous()
        cur = self.peek()
        next = self.peekNext()

        if prev.type == TT.Keyword:
            if prev.lexeme == "if":
                self.error(
                    "E1388",
                    f"Found a lonely 'if' keyword.",
                    prev,
                    HINT_IF,
                )
            elif prev.lexeme == "for":
                self.error(
                    "E1461",
                    f"Found a lonely 'for' keyword.",
                    prev,
                    HINT_FOR,
                )
            elif prev.lexeme == "while":
                self.error(
                    "E1174",
                    f"Found a lonely 'while' keyword.",
                    prev,
                    HINT_WHILE,
                )
            else:
                self.error(
                    "E1170",
                    f"Unexpected keyword.",
                    prev,
                    "An expression was expected, but got '{prev.lexeme}'.",
                )

        elif cur.type == TT.Indent:
            self.error(
                "E1572",
                f"Unexpected indentation.",
                cur,
                f"Code can only be indented after `do`  and `else`.",
            )

        else:
            self.error(
                "E1422",
                f"Expected expression after {prev.lexeme}.",
                prev,
                f"An expression was expected, but got '{cur.lexeme}'.",
            )

    def handleAssign(self, leftExpr, equalsToken, rightExpr, is_statement):
        if not is_statement and isinstance(rightExpr, tree.AssignExpr):
            self.error(
                "E1178",
                "Cannot multi-assign in expressions.",
                equalsToken,
                "You can do this in a statement:\n\n     a = b = c = 8\n",
                "But not in an expression.\n\n   foo = 3 + (a = b = 8)  # forbidden",
                throw=False,
            )
        # Handle the assignment target
        if isinstance(leftExpr, tree.VariableExpr):
            # Convert r-value expr into l-value assignment
            name = leftExpr.name
            return tree.AssignExpr(name, rightExpr)
        else:
            # Error, but no need to unwind, because we're not in a confused state
            self.error(
                "E1320",
                "Invalid assignment target.",
                leftExpr,
                "Cannot assign a value to this expression.",
                throw=False,
            )
            return leftExpr

    def finishCall(self, callee):
        arguments = []
        if self.match(TT.RightParen):
            pass  # no args
        else:
            while True:
                arguments.append(self.expression(allow_kw=True))
                if len(arguments) > 250:
                    self.error(
                        "E1068",
                        "Cannot have more than 250 arguments.",
                        self.peek(),
                        "For practical reasons, function calls cannot use more than 250 arguments.",
                    )
                hasComma = self.match(TT.Comma)
                if self.match(TT.RightParen):
                    break
                if not hasComma:
                    self.error(
                        "E1543",
                        "Expected ',' or ')' after argument.",
                        self.peek(),
                        "It looks like you forgot a comma in between two arguments.Perhaps you meant",
                    )

        return tree.CallExpr(callee, self.previous(), arguments)

    def ifExpr(self):
        # -> 'if' assignment 'its' assignment 'else' assignment
        ifToken = self.previous()
        condition = self.expression()
        if isinstance(condition, tree.AssignExpr):
            self.error(
                "E1162" "Bare assignment not allowed here.",
                condition,
                "To avoid the bug that '=' is used when '==' was intended,",
                f"it's required to compare the result of an assignment here.",
                throw=False,
            )
        if not self.matchKeyword("its"):
            self.error(
                "E1844",
                "Expected 'its' keyword.",
                self.peek(),
                "In an if-expression, the condition-expression must be followed with 'its'.",
            )
        return self.ifExpAfterIts(ifToken, condition)

    def ifExpAfterIts(self, ifToken, condition, *, couldBeStatement=False):
        if self.matchEos():
            hint = "Place the body right after `its`."
            if couldBeStatement:
                hint += " Or replace `its` with `do` to make this an if-statement`."
            self.error(
                "E1140",
                "An if-expression must be on a single line",
                self.peek(),
                hint,
                linesBefore=1,
            )
        thenExpression = self.expression()
        expr = tree.IfExpr(ifToken, condition, thenExpression, None)
        if not self.matchKeyword("else"):
            self.error(
                "E1870",
                "In an if-expression, the else-expression is required.",
                expr,
                "An if-expression produces a value (that's what it means to be an expression).",
                "Therefore, both branches must be defined.",
            )
        expr.elseExpr = self.expression()
        return expr

    def funcExpr(self, funcToken):
        # -> 'func' assignment
        # Note: cannot really re-use this in the funcStatement logic
        if not self.match(TT.LeftParen):
            self.error(
                "E1862",
                "Expected '(' directly after 'func' in expression-form.",
                self.peek(),
                "The expression form of function definitions are anonymous (a.ka. lambdas).",
                "The name must be omitted.",
            )
        params = self.funcParameters()

        if not self.matchKeyword("its"):
            self.error(
                "E1074",
                "Expected 'its' after signature of anonynous function",
                self.peek(),
            )
        if self.matchEos():
            self.error(
                "E1449",
                "A function expression must be on a single line.",
                self.peek(),
            )
        body = self.expression()

        name = ""  # in theory we could allow lambdas to have a name
        return tree.FunctionExpr(funcToken, name, params, body)

    def funcParameters(self):
        params = []
        if not self.match(TT.RightParen):
            while True:
                if not self.match(TT.Identifier):
                    self.error(
                        "E1846",
                        "Expected parameter name.",
                        self.peek(),
                        "The parameters of a function expression should be identifiers.",
                    )
                params.append(self.previous())
                if len(params) > 250:
                    self.error(
                        "E1462",
                        "Cannot have more than 250 parameters.",
                        self.previous(),
                        "This is a practical limitation, sorry!",
                    )
                hasComma = self.match(TT.Comma)
                if self.match(TT.RightParen):
                    break
                if not hasComma:
                    self.error(self.peek(), "Expecting ',' or ')' after argument.")
        return params
