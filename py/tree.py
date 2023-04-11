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
    def __init__(self, token, condition, thenBranch, elseBranch):
        self.token = token
        self.condition = condition
        self.thenBranch = thenBranch
        self.elseBranch = elseBranch


class loopIterStmt(Stmt):
    def __init__(self, token, var, iter, statements):
        self.token = token
        self.var = var
        self.iter = iter
        self.statements = statements


class loopWhileStmt(Stmt):
    def __init__(self, token, condition, statements):
        self.token = token
        self.condition = condition
        self.statements = statements


class PrintStmt(Stmt):
    def __init__(self, expr):
        self.expr = expr


class ExpressionStmt(Stmt):
    def __init__(self, expr):
        self.expr = expr


# %%


class Expr(ExprOrStmt):
    pass


class IfExpr(Expr):
    def __init__(self, token, condition, thenExpr, elseExpr):
        self.token = token
        self.condition = condition
        self.thenExpr = thenExpr
        self.elseExpr = elseExpr


class AssignExpr(Expr):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class VariableExpr(Expr):
    def __init__(self, name):
        self.name = name


class LogicalExpr(Expr):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class BinaryExpr(Expr):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class GroupingExpr(Expr):
    def __init__(self, expr):
        self.expr = expr


class RangeExpr(Expr):
    # Note: I think this expression is temporary, and should be resolved in a function call or something?
    def __init__(self, start, stop, step):
        self.start = start
        self.stop = stop
        self.step = step


class LiteralExpr(Expr):
    def __init__(self, token):
        self.token = token


class UnaryExpr(Expr):
    def __init__(self, op, right):
        self.op = op
        self.right = right
