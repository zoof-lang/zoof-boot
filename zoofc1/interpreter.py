import time

from .tokens import TT, Token


## Minilib


class ZoofRange:
    def __init__(self, start, stop, step=1):
        self.start = start
        self.stop = stop
        if step is None:
            step = 1
        assert step > 0
        self.step = step


class Callable:
    def arity(self):
        raise NotImplementedError()

    def call(self, interpreter, arguments):
        raise NotImplementedError()


class NativeCallable(Callable):
    pass


class Clock(NativeCallable):
    def arity(self):
        return 0

    def call(self, interpreter, arguments):
        return time.perf_counter()


class ArbitraryNumber(NativeCallable):
    def arity(self):
        return 0

    def call(self, interpreter, arguments):
        return 7.0  # not random, arbitrary! (consistent for tests)


class ZoofFunction(Callable):
    def __init__(self, declaration, closure):
        self.declaration = declaration
        self.closure = closure

    def arity(self):
        return len(self.declaration.params)

    def call(self, interpreter, arguments):
        environment = Environment(self.closure)
        for param, arg in zip(self.declaration.params, arguments):
            environment.set(param, arg)
        try:
            interpreter.executeBlock(self.declaration.body, environment)
        except Return as ret:
            return ret.value
        else:
            return None


##


class RuntimeErr(Exception):
    def __init__(self, token, message):
        super().__init__(message)
        self.token = token
        self.message = message


class Return(Exception):
    def __init__(self, value):
        super().__init__()
        self.value = value


class Environment:
    def __init__(self, parent):
        self.parent = parent
        self.map = {}

    def set(self, name: Token, value):
        self.map[name.lexeme] = value

    def get(self, name: Token):
        try:
            return self.map[name.lexeme]
        except KeyError:
            if self.parent:
                return self.parent.get(name)
            else:
                raise RuntimeErr(name, f"Undefined variable '{name.lexeme}'.")


class InterpreterVisitor:
    def __init__(self, print, handler):
        self.print = print
        self.handler = handler
        self.globals = Environment(None)
        self.env = Environment(self.globals)
        self.loadGlobals()

    def loadGlobals(self):
        self.globals.map["clock"] = Clock()
        self.globals.map["arbitraryNumber"] = ArbitraryNumber()

    def interpret(self, statements):
        try:
            val = None
            for statement in statements:
                val = self.execute(statement)
            # Print the last value if it was an expression-statement
            if val is not None:
                self.print(self.stringify(val))
        except RuntimeErr as err:
            self.handler.runtimeError(err.token, err.message)
        except Exception as err:
            raise err

    def executeBlock(self, statements, environment):
        original_environment = self.env
        try:
            self.env = environment
            for stmt in statements:
                self.execute(stmt)
        finally:
            self.env = original_environment

    def exececuteMultiple(self, statements):
        for stmt in statements:
            self.execute(stmt)

    def execute(self, stmt):
        return stmt.accept(self)

    def evaluate(self, expr):
        return expr.accept(self)

    def isTruethy(self, value, token):
        if value == False:
            return False
        elif value == True:
            return True
        else:
            typename = value.__class__.__name__
            raise RuntimeErr(token, f"Cannot convert {typename} to bool.")

    def checkNumberOperand(self, op, right):
        if not isinstance(right, float):
            classname = right.__class__.__name__
            raise RuntimeErr(
                op.token, f"Unary operand must be a number, not '{classname}'"
            )

    def checkNumberOperands(self, op, left, right):
        if not isinstance(left, float):
            classname = left.__class__.__name__
            raise RuntimeErr(op, f"Left operand must be a number, not '{classname}'")
        if not isinstance(right, float):
            classname = right.__class__.__name__
            raise RuntimeErr(op, f"Right operand must be a number, not '{classname}'")

    def isEqual(self, left, right):
        if left is None and right is None:
            return True
        else:
            return left == right

    def stringify(self, value):
        if value is None:
            return "nil"
        elif isinstance(value, bool):
            return "true" if value else "false"
        else:
            return repr(value)

    # %%

    def visitBlockStmt(self, stmt):
        self.executeBlock(stmt.statements, Environment(self.env))

    def visitIfStmt(self, stmt):
        if self.isTruethy(self.evaluate(stmt.condition), None):
            self.exececuteMultiple(stmt.thenBranch)
        else:
            self.exececuteMultiple(stmt.elseBranch)

    def visitWhileStmt(self, stmt):
        while self.isTruethy(self.evaluate(stmt.condition), stmt.token):
            self.exececuteMultiple(stmt.statements)

    def visitForStmt(self, stmt):
        iter = self.evaluate(stmt.iter)
        assert isinstance(iter, ZoofRange)
        value = iter.start
        while value < iter.stop:
            self.env.set(stmt.var.name, value)
            self.exececuteMultiple(stmt.statements)
            value += iter.step

    def visitBreakStmt(self, stmt):
        raise RuntimeErr(stmt.token, "break is not yet implemented.")

    def visitPrintStmt(self, stmt):
        value = self.evaluate(stmt.expr)
        self.print(self.stringify(value))

    def visitFunctionStmt(self, stmt):
        function = ZoofFunction(stmt, self.env)
        self.env.set(stmt.name, function)

    def visitReturnStmt(self, stmt):
        if stmt.value is None:
            value = None
        else:
            value = self.evaluate(stmt.value)
        raise Return(value)

    def visitExpressionStmt(self, stmt):
        return self.evaluate(stmt.expr)

    # %%

    def visitVariableExpr(self, expr):
        return self.env.get(expr.name)

    def visitIfExpr(self, expr):
        if self.isTruethy(self.evaluate(expr.condition), None):
            return self.evaluate(expr.thenExpr)
        else:
            self.evaluate(expr.elseExpr)

    def visitGroupingExpr(self, expr):
        return self.evaluate(expr.expr)

    def visitAssignExpr(self, expr):
        value = self.evaluate(expr.value)
        self.env.set(expr.name, value)
        return value

    def visitRangeExpr(self, expr):
        return ZoofRange(
            self.evaluate(expr.start),
            self.evaluate(expr.stop),
            self.evaluate(expr.step),
        )

    def visitLiteralExpr(self, expr):
        t = expr.token.type
        if t == TT.LiteralNil:
            return None
        elif t == TT.LiteralTrue:
            return True
        elif t == TT.LiteralFalse:
            return False
        elif t == TT.LiteralNumber:
            return float(expr.token.lexeme)
        elif t == TT.LiteralString:
            return expr.token.lexeme[1:-1]
        else:
            raise RuntimeErr(expr.token, f"Unexpected literal: '{expr.token.lexeme}'")

    def visitUnaryExpr(self, expr):
        right = self.evaluate(expr.right)
        if expr.op.type == TT.Minus:
            self.checkNumberOperand(expr.op, right)
            return -right
        if expr.op.type == TT.Plus:
            self.checkNumberOperand(expr.op, right)
            return right
        else:
            raise RuntimeErr(expr.op, f"Unexpected unary operation.")

    def visitLogicalExpr(self, expr):
        left = self.evaluate(expr.left)
        opname = expr.op.lexeme
        if opname == "or":
            if self.isTruethy(left, expr.op):
                return left
            return self.evaluate(expr.right)
        elif opname == "and":
            if not self.isTruethy(left, expr.op):
                return left
            return self.evaluate(expr.right)
        else:
            raise RuntimeErr(expr.op, f"Unexpected logical expr '{optype}'")

    def visitBinaryExpr(self, expr):
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)
        optype = expr.op.type
        # Numeric
        if optype == TT.Minus:
            self.checkNumberOperands(expr.op, left, right)
            return left - right
        elif optype == TT.Slash:
            self.checkNumberOperands(expr.op, left, right)
            return left / right
        elif optype == TT.Star:
            self.checkNumberOperands(expr.op, left, right)
            return left * right
        elif optype == TT.Caret:
            self.checkNumberOperands(expr.op, left, right)
            return left**right
        elif optype == TT.Plus:
            if isinstance(left, float) and isinstance(right, float):
                return left + right
            elif isinstance(left, str) and isinstance(right, str):
                return left + right
            else:
                classname1 = left.__class__.__name__
                classname2 = right.__class__.__name__
                raise RuntimeErr(
                    expr.op, f"Cannot add '{classname1}' and '{classname2}'"
                )
        # Comparisons
        elif optype == TT.Greater:
            self.checkNumberOperands(expr.op, left, right)
            return left > right
        elif optype == TT.GreaterEqual:
            self.checkNumberOperands(expr.op, left, right)
            return left >= right
        elif optype == TT.Less:
            self.checkNumberOperands(expr.op, left, right)
            return left < right
        elif optype == TT.LessEqual:
            self.checkNumberOperands(expr.op, left, right)
            return left <= right
        # Equality
        elif optype == TT.EqualEqual:
            return self.isEqual(left, right)
        elif optype == TT.BangEqual:
            return not self.isEqual(left, right)
        else:
            raise RuntimeErr(expr.op, f"Unexpected binary expr '{optype}'")

    def visitCallExpr(self, expr):
        callee = self.evaluate(expr.callee)
        arguments = [self.evaluate(argExpr) for argExpr in expr.arguments]

        # todo: error is bound to the closing paren :/
        if not isinstance(callee, Callable):
            raise RuntimeErr(expr.paren, "not a callable object.")
        elif callee.arity() != len(arguments):
            raise RuntimeErr(
                expr.paren,
                f"Expected {callee.arity()} arguments, but got {len(arguments)}",
            )

        return callee.call(self, arguments)
