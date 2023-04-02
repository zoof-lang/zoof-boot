from tokens import TT


class RuntimeErr(Exception):
    def __init__(self, token, message):
        super().__init__(message)
        self.token = token
        self.message = message


class InterpreterVisitor:
    def __init__(self, handler):
        self.handler = handler

    def interpret(self, expr):
        try:
            result = self.evaluate(expr)
            print(self.stringify(result))
        except RuntimeErr as err:
            self.handler.runtimeError(err.token, err.message)
        except Exception as err:
            raise err

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

    def isEqual(left, right):
        if left is None and right is None:
            return True
        else:
            return left == right

    def stringify(self, value):
        if value is None:
            return "nil"
        else:
            return repr(value)

    def visitGroupingExpr(self, expr):
        return self.evaluate(expr.expr)

    def visitLiteralExpr(self, expr):
        s = expr.token.lexeme
        if s[0] in "0123456789":
            return float(s)
        elif s.startswith("'"):
            return s[1:-1]
        else:
            raise RuntimeErr(expr.token, f"Unexpected literal: '{s}'")

    def visitUnaryExpr(self, expr):
        right = self.evaluate(expr)
        if expr.op.type == TT.Minus:
            self.checkNumberOperand(expr.op, right)
            return -right
        elif expr.op.type == TT.Bang:  # todo: must use "not"
            return not self.isTruethy(expr.op, right)
        else:
            raise RuntimeErr(expr.op, f"Unexpected unary operation.")

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
