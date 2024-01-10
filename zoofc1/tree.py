class ExprOrStmt:
    def accept(self, visitor):
        methodName = "visit" + self.__class__.__name__
        method = getattr(visitor, methodName, None)
        if method is None:
            raise NotImplementedError(methodName)
        else:
            return method(self)

    def location(self):
        raise NotImplementedError()  # ((line1, col1), (line2, col2))


# %%


class Stmt(ExprOrStmt):
    def location(self):
        # Implementation that works for most statements
        token = self.token
        offset = len(self.token.lexeme)
        return (token.line, token.column), (token.line, token.column + offset)


class Program(Stmt):
    def __init__(self, statements):
        self.statements = statements

    def location(self):
        return (self.statements[0].location()[0], self.statements[-1].location()[1])


class PrintStmt(Stmt):
    def __init__(self, token, expr):
        self.token = token
        self.expr = expr


class DoStmt(Stmt):
    def __init__(self, token, statements):
        self.token = token
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


class ReturnStmt(Stmt):
    def __init__(self, token, value):
        self.token = token
        self.value = value


class FunctionStmt(Stmt):
    def __init__(self, token, name, params, statements):
        self.token = token
        self.name = name
        self.params = params
        self.body = statements  # nil if abstract, list for stmt, expr for expr-func
        self.kind = self.token.lexeme  # func, method, getter, setter


class StructStmt(Stmt):
    def __init__(self, token, name, fields, functions: list):
        self.token = token
        self.name = name
        self.fields = fields
        self.functions = functions


class TraitStmt(Stmt):
    def __init__(self, token, name, functions: list):
        self.token = token
        self.name = name
        self.functions = functions


class ImplStmt(Stmt):
    def __init__(self, token, trait, struct, functions: list):
        self.token = token
        self.trait = trait
        self.struct = struct
        self.functions = functions


class ExpressionStmt(Stmt):
    def __init__(self, expr):
        self.expr = expr

    def location(self):
        return self.expr.location()


# %%


class Expr(ExprOrStmt):
    pass


class IfExpr(Expr):
    def __init__(self, token, condition, thenExpr, elseExpr):
        self.token = token
        self.condition = condition
        self.thenExpr = thenExpr
        self.elseExpr = elseExpr

    def location(self):
        loc1 = self.token.line, self.token.column
        if self.elseExpr is None:
            # this should not happen in theory, but when it does
            # the error handler uses this code path :)
            loc2 = self.thenExpr.location()[1]
        else:
            loc2 = self.elseExpr.location()[1]
        return loc1, loc2


class FunctionExpr(Expr):
    def __init__(self, token, name, params, expr):
        self.token = token
        self.name = name
        self.params = params
        self.body = expr
        self.kind = self.token.lexeme  # func, method, getter, setter

    def location(self):
        loc1 = self.token.line, self.token.column
        loc2 = self.body.location()[1]
        return loc1, loc2


class AssignExpr(Expr):
    def __init__(self, name, value):
        self.name = name  # a token
        self.value = value  # Can be None

    def location(self):
        loc1 = self.name.line, self.name.column
        if self.value is None:
            loc2 = loc1[0], loc1[1] + len(self.name.lexeme)
        else:
            loc2 = self.value.location()[1]
        return loc1, loc2


class VariableExpr(Expr):
    def __init__(self, name):
        self.name = name
        self.depth = -9  # set by resolver

    def location(self):
        loc1 = self.name.line, self.name.column
        loc2 = loc1[0], loc1[1] + len(self.name.lexeme)
        return loc1, loc2


class LogicalExpr(Expr):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def location(self):
        loc1 = self.left.location()[0]
        loc2 = self.right.location()[1]
        return loc1, loc2


class BinaryExpr(Expr):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def location(self):
        loc1 = self.left.location()[0]
        loc2 = self.right.location()[1]
        return loc1, loc2


class GroupingExpr(Expr):
    def __init__(self, expr):
        self.expr = expr

    def location(self):
        return self.expr.location()


class GetExpr(Expr):
    def __init__(self, token, object, name):
        self.token = token
        self.object = object
        self.name = name

    def location(self):
        loc1 = self.object.location()[0]
        loc2 = self.name.line, self.name.column + len(self.name.lexeme)
        return loc1, loc2


class SetExpr(Expr):
    def __init__(self, token, object, name, value):
        self.token = token
        self.object = object
        self.name = name
        self.value = value

    def location(self):
        loc1 = self.object.location()[0]
        loc2 = self.name.line, self.name.column + len(self.name.lexeme)
        return loc1, loc2


class RangeExpr(Expr):
    # Note: I think this expression is temporary, and should be resolved in a function call or something?
    def __init__(self, start, stop, step):
        self.start = start
        self.stop = stop
        self.step = step

    def location(self):
        loc1 = self.start.location()[0]
        if self.step is None:
            loc2 = self.stop.location()[1]
        else:
            loc2 = self.step.location()[1]
        return loc1, loc2


class CallExpr(Expr):
    def __init__(self, callee, paren, arguments):
        self.callee = callee
        self.paren = paren  # the closing one
        self.arguments = arguments

    def location(self):
        loc1 = self.callee.location()[0]
        loc2 = self.paren.line, self.paren.column
        return loc1, loc2


class LiteralExpr(Expr):
    def __init__(self, token):
        self.token = token

    def location(self):
        loc1 = self.token.line, self.token.column
        loc2 = loc1[0], loc1[1] + len(self.token.lexeme)
        return loc1, loc2


class UnaryExpr(Expr):
    def __init__(self, op, right):
        self.op = op
        self.right = right

    def location(self):
        loc1 = self.op.line, self.op.column
        loc2 = self.right.location()[1]
        return loc1, loc2
