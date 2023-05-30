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
    def __init__(self, declaration, closure, source):
        self.declaration = declaration
        self.closure = closure
        self.source = source
        self.freeVars = self.declaration.freeVars.copy()
        self.captured = {}

    def arity(self):
        return len(self.declaration.params)

    def popEnvironment(self, environment):
        # This is where we would capture the free variables, if we were
        # to support closures.
        toPop = set()
        for name, expr in self.freeVars.items():
            if name in environment.map:
                toPop.add(name)
                self.captured[name] = expr
        for name in toPop:
            self.freeVars.pop(name)
        # Be good for memory
        environment.map.clear()

    def call(self, interpreter, arguments):
        if self.captured:
            expr = list(self.captured.values())[0]
            raise RuntimeErr(expr.name, "Closures are not supported at the moment.")
        environment = Environment(self.closure)
        # for name, value in self.captured.items():
        #     environment.set(name, value)
        for param, arg in zip(self.declaration.params, arguments):
            environment.set(param, arg)

        prevSource = interpreter.ehandler.swapSource(self.source)
        try:
            if isinstance(self.declaration.body, list):
                # Declaration function
                try:
                    interpreter.executeBlock(self.declaration.body, environment)
                except Return as ret:
                    return ret.value
                else:
                    return None
            else:
                # A lambda / expression function
                return interpreter.executeBlock(self.declaration.body, environment)
        finally:
            interpreter.ehandler.swapSource(prevSource)


BUILTINS = {}
BUILTINS["clock"] = Clock()
BUILTINS["arbitraryNumber"] = ArbitraryNumber()

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


class Break(Exception):
    pass


class Environment:
    def __init__(self, parent):
        self.parent = parent
        self.index = 0 if parent is None else parent.index + 1
        self.map = {}
        self.loopStack = []

    def set(self, name: Token, value):
        self.map[name.lexeme] = value

    def get(self, name: Token):
        try:
            return self.map[name.lexeme]
        except KeyError:
            raise RuntimeErr(name, f"Undefined variable '{name.lexeme}'.")


class InterpreterVisitor:
    def __init__(self, print, ehandler):
        self.print = print
        self.ehandler = ehandler
        builtins = Environment(None)
        builtins.map.update(BUILTINS)
        self.env = Environment(builtins)
        self.maybeClosures = []

    def interpret(self, program):
        """Interpret the given program."""
        # Init
        self.ehandler.swapSource(program.source)

        try:
            val = None
            for statement in program.statements:
                val = self.execute(statement)
            # Print the last value if it was an expression-statement
            if val is not None:
                self.print(self.stringify(val))
        except RuntimeErr as err:
            self.ehandler.runtimeError(err.token, err.message)
        except Exception as err:
            raise err

    def executeBlock(self, body, environment):
        # todo: only really used for functions!
        original_env = self.env
        self.env = environment
        self.maybeClosures.append([])
        try:
            if isinstance(body, list):
                for stmt in body:
                    self.execute(stmt)
            else:
                return self.evaluate(body)
        finally:
            if self.maybeClosures:
                for func in self.maybeClosures.pop(-1):
                    func.popEnvironment(self.env)
            self.env = original_env

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

    def visitDoStmt(self, stmt):
        self.exececuteMultiple(stmt.statements)

    def visitIfStmt(self, stmt):
        if self.isTruethy(self.evaluate(stmt.condition), stmt.token):
            self.exececuteMultiple(stmt.thenBranch)
        else:
            self.exececuteMultiple(stmt.elseBranch)

    def visitWhileStmt(self, stmt):
        self.env.loopStack.append(True)
        try:
            while self.isTruethy(self.evaluate(stmt.condition), stmt.token):
                self.exececuteMultiple(stmt.statements)
        except Break:
            pass
        self.env.loopStack.pop(-1)

    def visitForStmt(self, stmt):
        iter = self.evaluate(stmt.iter)
        assert isinstance(iter, ZoofRange)
        value = iter.start
        self.env.loopStack.append(True)
        try:
            while value < iter.stop:
                self.env.set(stmt.var.name, value)
                self.exececuteMultiple(stmt.statements)
                value += iter.step
        except Break:
            pass
        self.env.loopStack.pop(-1)

    def visitBreakStmt(self, stmt):
        if not self.env.loopStack:
            raise RuntimeErr(
                stmt.token, "Can only break inside a for-loop or while-loop."
            )
        else:
            raise Break()

    def visitPrintStmt(self, stmt):
        value = self.evaluate(stmt.expr)
        self.print(self.stringify(value))

    def visitFunctionStmt(self, stmt):
        function = ZoofFunction(stmt, self.env, self.ehandler.source)
        self.env.set(stmt.name, function)
        if self.maybeClosures:
            self.maybeClosures[-1].append(function)

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
        env = self.env
        assert expr.depth >= 0
        while env.index > 0 and env.index > expr.depth:
            env = env.parent
        return env.get(expr.name)

    def visitIfExpr(self, expr):
        if self.isTruethy(self.evaluate(expr.condition), None):
            return self.evaluate(expr.thenExpr)
        else:
            return self.evaluate(expr.elseExpr)

    def visitFunctionExpr(self, expr):
        function = ZoofFunction(expr, self.env, self.ehandler.source)
        if self.maybeClosures:
            self.maybeClosures[-1].append(function)
        return function

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
            None if expr.step is None else self.evaluate(expr.step),
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
