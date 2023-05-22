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
    def __init__(self, ehandler):
        self.ehandler = ehandler
        builtin_scope = Scope({name for name in BUILTINS.keys()})
        self.scopes = [builtin_scope]
        self.unresolvedFunctions = {}

        # Start main scope
        self.beginScope()

    def error(self, token, message):
        self.ehandler.nameError(token, message)

    def resolveProgram(self, program):
        """Resolve the names in the given program.

        Can be called multiple times for different programs that execute
        in the same scope.
        """
        # Init
        assert len(self.scopes) == 2, "trying to resolve with a closed resolver"
        self.ehandler.swapSource(program.source)

        self.resolveStatements(program.statements)
        self.resolveRemainingFunctions()

    def resolveStatements(self, statements):
        for stmt in statements:
            self.resolve(stmt)

    def resolve(self, stmt_or_expr):
        assert isinstance(stmt_or_expr, (Stmt, Expr))
        stmt_or_expr.accept(self)

    def resolveRemainingFunctions(self):
        for nameStr in list(self.unresolvedFunctions.keys()):
            self.checkFunction(nameStr)
        assert not self.unresolvedFunctions

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

    def beginScope(self):
        self.scopes.append(Scope())

    def endScope(self):
        self.resolveRemainingFunctions()
        self.scopes.pop(-1)

    def declare(self, name):
        if name.lexeme in self.scopes[-1].freeVars:
            expr = self.scopes[-1].freeVars[name.lexeme]
            self.error(
                expr.name,
                "Variable is used before it's defined in this scope (cannot use a variable that is shadowed in the same scope).",
            )

        self.scopes[-1].add(name.lexeme)

    # %% The interesting bits

    def visitDoStmt(self, stmt):
        self.resolveStatements(stmt.statements)

    def visitFunctionStmt(self, stmt):
        self.declare(stmt.name)
        self.unresolvedFunctions[stmt.name.lexeme] = stmt

    def visitFunctionExpr(self, expr):
        # Check it directly
        self.unresolvedFunctions[""] = expr
        self.checkFunction("")

    def checkFunction(self, name):
        declaration = self.unresolvedFunctions.pop(name, None)
        if declaration is not None:
            self.beginScope()
            for param in declaration.params:
                self.declare(param)
            if isinstance(declaration.body, list):
                self.resolveStatements(declaration.body)
            else:
                self.resolve(declaration.body)
            declaration.freeVars = {
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

    def visitCallExpr(self, expr):
        self.resolve(expr.callee)
        if isinstance(expr.callee, VariableExpr):
            self.checkFunction(expr.callee.name.lexeme)
        for arg in expr.arguments:
            self.resolve(arg)

    # %% The boring stmt's

    def visitExpressionStmt(self, stmt):
        self.resolve(stmt.expr)

    def visitIfStmt(self, stmt):
        self.resolve(stmt.condition)
        self.resolveStatements(stmt.thenBranch)
        if stmt.elseBranch is not None:
            self.resolveStatements(stmt.elseBranch)

    def visitWhileStmt(self, stmt):
        self.resolve(stmt.condition)
        self.resolveStatements(stmt.statements)

    def visitForStmt(self, stmt):
        self.resolve(stmt.iter)
        self.resolve(stmt.var)
        self.resolveStatements(stmt.statements)

    def visitBreakStmt(self, stmt):
        pass

    def visitReturnStmt(self, stmt):
        if stmt.value is not None:
            self.resolve(stmt.value)

    def visitPrintStmt(self, stmt):
        self.resolve(stmt.expr)

    # %% The boring expr's

    def visitIfExpr(self, expr):
        self.resolve(expr.condition)
        self.resolve(expr.thenExpr)
        self.resolve(expr.elseExpr)

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

    def visitGroupingExpr(self, expr):
        self.resolve(expr.expr)

    def visitLiteralExpr(self, expr):
        pass
