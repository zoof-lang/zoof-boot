from .tree import Stmt, Expr, VariableExpr
from .interpreter import BUILTINS

# Scope 0: current scope
# Scope 1: one level deeper
# Scope n: ...
# Scope globals:
# Scope builtins:


class Scope:
    def __init__(self, names=None):
        self.names = names or set()
        self.freeVars = {}

    def contains(self, name):
        return name in self.names

    def add(self, name):
        self.names.add(name)


class ResolverVisitor:
    def __init__(self, interpreter, ehandler):
        self.interpreter = interpreter
        self.ehandler = ehandler
        self.scopes = [Scope({name for name in BUILTINS.keys()})]
        # We delay resolving functions until they're called or scope is left
        self.unresolvedFunctions = {}

    def error(self, token, message):
        self.ehandler.syntaxError(token, message)

    def resolve_program(self, statements):
        # todo: visitBlockStmt
        self.beginScope()
        self.resolve_statements(statements)
        self.endScope()

    def resolve_statements(self, statements):
        for stmt in statements:
            self.resolve(stmt)

    def resolve(self, stmt_or_expr):
        assert isinstance(stmt_or_expr, (Stmt, Expr))
        stmt_or_expr.accept(self)

    def beginScope(self):
        self.scopes.append(Scope())

    def endScope(self):
        for nameStr in list(self.unresolvedFunctions.keys()):
            self.checkFunction(nameStr)
        assert not self.unresolvedFunctions
        self.scopes.pop(-1)

    def declare(self, name):
        if name.lexeme in self.scopes[-1].freeVars:
            expr = self.scopes[-1].freeVars[name.lexeme]
            self.error(
                expr.name,
                "Variable is used before it's defined in this scope (cannot use a variable that is shadowed in the same scope).",
            )

        self.scopes[-1].add(name.lexeme)

    def resolveLocal(self, expr):
        name = expr.name
        expr.depth = -1
        for depth, scope in enumerate(self.scopes):
            if scope.contains(name.lexeme):
                expr.depth = depth
        if expr.depth == -1:
            self.error(name, f"Undefined variable")
        elif expr.depth == len(self.scopes) - 1:
            pass  # a local
        else:
            # A free variable, in the liberal sense. It can still be a global or
            # builtin, but for the logic in declare() we need to include *all* non-locals.
            freeVars = self.scopes[-1].freeVars
            if name.lexeme not in freeVars:
                freeVars[name.lexeme] = expr

    # %% The interesting bits

    def visitBlockStmt(self, stmt):
        self.beginScope()
        self.resolve_statements(stmt.statements)
        self.endScope()

    def visitFunctionStmt(self, stmt):
        self.declare(stmt.name)
        self.unresolvedFunctions[stmt.name.lexeme] = stmt

    def checkFunction(self, name):
        stmt = self.unresolvedFunctions.pop(name, None)
        if stmt is not None:
            self.beginScope()
            for param in stmt.params:
                self.declare(param)
            self.resolve_statements(stmt.body)
            stmt.freeVars = {
                name: expr
                for name, expr in self.scopes[-1].freeVars.items()
                if expr.depth >= 1
            }
            self.endScope()

    def visitAssignExpr(self, expr):
        if expr.value is not None:
            self.resolve(expr.value)
        self.declare(expr.name)
        # When a variable is assigned, it's *always* in the local scope in Zoof

    def visitVariableExpr(self, expr):
        self.resolveLocal(expr)

    # %% The boring stmt's

    def visitExpressionStmt(self, stmt):
        self.resolve(stmt.expr)

    def visitIfStmt(self, stmt):
        self.resolve(stmt.condition)
        self.resolve_statements(stmt.thenBranch)
        if stmt.elseBranch is not None:
            self.resolve_statements(stmt.elseBranch)

    def visitWhileStmt(self, stmt):
        self.resolve(stmt.condition)
        self.resolve_statements(stmt.statements)

    def visitForStmt(self, stmt):
        self.resolve(stmt.iter)
        self.resolve(stmt.var)
        self.resolve_statements(stmt.statements)

    def visitBreakStmt(self, stmt):
        pass

    def visitReturnStmt(self, stmt):
        if stmt.value is not None:
            self.resolve(stmt.value)

    def visitPrintStmt(self, stmt):
        self.resolve(stmt.expr)

    # %% The boring expr's

    def visitBinaryExpr(self, expr):
        self.resolve(expr.left)
        self.resolve(expr.right)

    def visitLogicalExpr(self, expr):
        self.resolve(expr.left)
        self.resolve(expr.right)

    def visitUnaryExpr(self, expr):
        self.resolve(expr.right)

    def visitRangeExpr(self, expr):
        self.resolve(expr.start)
        self.resolve(expr.stop)
        self.resolve(expr.step)

    def visitCallExpr(self, expr):
        self.resolve(expr.callee)
        if isinstance(expr.callee, VariableExpr):
            self.checkFunction(expr.callee.name.lexeme)
        for arg in expr.arguments:
            self.resolve(arg)

    def visitGroupingExpr(self, expr):
        self.resolve(expr.expr)

    def visitLiteralExpr(self, expr):
        pass
