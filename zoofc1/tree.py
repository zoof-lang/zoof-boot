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


class Program(Stmt):
    def __init__(self, statements):
        self.statements = statements


class DoStmt(Stmt):
    def __init__(self, statements):
        self.statements = statements


class IfStmt(Stmt):
    def __init__(self, token, condition, thenBranch, elseBranch):
        self.token = token
        self.condition = condition
        self.thenBranch = thenBranch
        self.elseBranch = elseBranch


class ForStmt(Stmt):
    def __init__(self, token, var, iter, statements):
        self.token = token
        self.var = var
        self.iter = iter
        self.statements = statements


class WhileStmt(Stmt):
    def __init__(self, token, condition, statements):
        self.token = token
        self.condition = condition
        self.statements = statements


class BreakStmt(Stmt):
    def __init__(self, token):
        self.token = token


class PrintStmt(Stmt):
    def __init__(self, expr):
        self.expr = expr


class ExpressionStmt(Stmt):
    def __init__(self, expr):
        self.expr = expr


class FunctionStmt(Stmt):
    def __init__(self, name, params, statements):
        self.name = name
        self.params = params
        self.body = statements


class ReturnStmt(Stmt):
    def __init__(self, keyword, value):
        self.keyword = keyword
        self.value = value


# %%


class Expr(ExprOrStmt):
    pass


class IfExpr(Expr):
    def __init__(self, token, condition, thenExpr, elseExpr):
        self.token = token
        self.condition = condition
        self.thenExpr = thenExpr
        self.elseExpr = elseExpr


class FunctionExpr(Expr):
    def __init__(self, name, params, expr):
        self.name = name
        self.params = params
        self.body = expr


class AssignExpr(Expr):
    def __init__(self, name, value):
        self.name = name
        self.value = value  # Can be None


class VariableExpr(Expr):
    def __init__(self, name):
        self.name = name
        self.depth = -9  # set by resolver


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


class CallExpr(Expr):
    def __init__(self, callee, paren, arguments):
        self.callee = callee
        self.paren = paren  # the closing one
        self.arguments = arguments


class LiteralExpr(Expr):
    def __init__(self, token):
        self.token = token


class UnaryExpr(Expr):
    def __init__(self, op, right):
        self.op = op
        self.right = right
