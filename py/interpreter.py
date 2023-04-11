from tokens import TT, Token


## Minilib


class ZoofRange:
    def __init__(self, start, stop, step=1):
        self.start = start
        self.stop = stop
        if step is None:
            step = 1
        assert step > 0
        self.step = step


##


class RuntimeErr(Exception):
    def __init__(self, token, message):
        super().__init__(message)
        self.token = token
        self.message = message


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
    def __init__(self, handler):
        self.handler = handler
        self.env = Environment(None)

    def interpret(self, statements):
        try:
            val = None
            for statement in statements:
                val = self.execute(statement)
            if val is not None:
                print(val)  # todo: is this the right way to print the last value?
        except RuntimeErr as err:
            self.handler.runtimeError(err.token, err.message)
        except Exception as err:
            raise err

    def executeBock(self, statements, environment):
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
        else:
            return repr(value)

    # %%

    def visitBlockStmt(self, stmt):
        self.executeBock(stmt.statements, Environment(self.env))

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

    def visitPrintStmt(self, stmt):
        value = self.evaluate(stmt.expr)
        print(self.stringify(value))

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
                raise RuntimeErr(expr.op, f"Cannot add '{classname1}' and {classname2}")
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
