class ExprOrStmt:
    def accept(self, visitor):
        raise NotImplementedError()

    def accept(self, visitor):
        methodName = "visit" + self.__class__.__name__
        method = getattr(visitor, methodName, None)
        if method is None:
            raise NotImplementedError(methodName)
        else:
            return method(self)


# %%


class Stmt(ExprOrStmt):
    pass


class BlockStmt(Stmt):
    def __init__(self, statements):
        self.statements = statements


class IfStmt(Stmt):
    def __init__(self, condition, thenBranch, elseBranch):
        self.condition = condition
        self.thenBranch = thenBranch
        self.elseBranch = elseBranch


class PrintStmt(Stmt):
    def __init__(self, expr):
        self.expr = expr


class ExpressionStmt(Stmt):
    def __init__(self, expr):
        self.expr = expr


# %%


class Expr(ExprOrStmt):
    pass


class AssignExpr(Expr):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class VariableExpr(Expr):
    def __init__(self, name):
        self.name = name


class IfExpr(Expr):
    def __init__(self, condition, thenExpr, elseExpr):
        self.condition = condition
        self.thenExpr = thenExpr
        self.elseExpr = elseExpr


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
