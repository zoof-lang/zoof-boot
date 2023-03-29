class Expr:
    def accept(self, visitor):
        raise NotImplementedError()

    def accept(self, visitor):
        method = getattr(visitor, "visit" + self.__class__.__name__)
        return method(self)


class BinaryExpr(Expr):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class GroupingExpr(Expr):
    def __init__(self, expr):
        self.expr = expr


class LiteralExpr(Expr):
    def __init__(self, token):
        self.token = token


class UnaryExpr(Expr):
    def __init__(self, op, right):
        self.op = op
        self.right = right


class Visitor:
    pass
