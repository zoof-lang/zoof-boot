from .tree import Stmt, Expr, VariableExpr
from .interpreter import BUILTINS

# Scope 0: current scope
# Scope 1: one level deeper
# Scope n: ...
# Scope globals:
# Scope builtins:


class Scope:
    def __init__(self, names=None):
        # Names of variables that exist in the current scope
        self.names = names or set()
        # Names that are used in this scope but declared in an outer scope
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
        # To help support late binding
        self.unresolvedFunctions = {}

        # Start main scope
        self.beginScope()

    def error(self, errorCode, token, message, *explanation, throw=True, **kwargs):
        explanation = "\n".join(explanation)
        self.ehandler.nameError(errorCode, token, message, explanation, **kwargs)

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

    def checkFunction(self, name):
        declaration = self.unresolvedFunctions.pop(name, None)
        if declaration is not None:
            self.resolveFunction(declaration)

    def resolveRemainingFunctions(self):
        for declaration in self.unresolvedFunctions.values():
            self.resolveFunction(declaration)
        self.unresolvedFunctions = {}

    def resolveLocal(self, expr):
        """Resolve the local usage of a variable, determining its depth in the scope-stack."""
        name = expr.name
        expr.depth = -1
        for depth, scope in enumerate(self.scopes):
            if scope.contains(name.lexeme):
                expr.depth = depth
        if expr.depth == -1:
            self.error(
                "E2359",
                f"Undefined variable.",
                name,
                "This variable name is used before it is defined.",
            )
        elif expr.depth == len(self.scopes) - 1:
            pass  # a local
        else:
            # A free variable, in the liberal sense: it can be a nonlocal, global or
            # builtin. For the logic in declare() we need to include *all* non-locals.
            freeVars = self.scopes[-1].freeVars
            if name.lexeme not in freeVars:
                freeVars[name.lexeme] = expr

    def beginScope(self):
        self.scopes.append(Scope())

    def endScope(self):
        self.resolveRemainingFunctions()
        self.scopes.pop(-1)

    def declare(self, name):
        """Declare that a variable with the given name exists from this point on."""

        # Check that the name is not already used and addresses a variable from an outer scope
        freeVars = self.scopes[-1].freeVars
        if name.lexeme in freeVars:
            expr = freeVars[name.lexeme]
            self.error(
                "E2446",
                "Variable is used before it's declared in this scope.",
                expr.name,
                "There is a variable in an outer scope with the same name,",
                "but it is also defined later in the current scope (i.e. shadowed).",
                "You must either rename the latter, to avoid shadowing, or define",
                "the local variable before it is used here.",
            )

        # Declare the variable to exist in this scope
        self.scopes[-1].add(name.lexeme)

    # %% The interesting bits

    def visitDoStmt(self, stmt):
        self.resolveStatements(stmt.statements)

    def visitStructStmt(self, stmt):
        self.declare(stmt.name)

    def visitImplStmt(self, stmt):
        for fn in stmt.functions:
            self.resolveFunction(fn, extra_names=["this", "This"])

    def visitFunctionStmt(self, stmt):
        # todo: prevent defining the same funcion twice in the same source. But do alow re-defining in an interactive session.
        self.declare(stmt.name)
        self.unresolvedFunctions[stmt.name.lexeme] = stmt

    def visitFunctionExpr(self, expr):
        self.resolveFunction(expr)

    def resolveFunction(self, declaration, extra_names=()):
        self.beginScope()
        for name in extra_names:
            self.scopes[-1].add(name)
        for param in declaration.params:
            self.declare(param)
        if isinstance(declaration.body, list):
            self.resolveStatements(declaration.body)
        else:
            self.resolve(declaration.body)
        # Add freeVars to the AST node, so the interpreter can create precise closures
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

    def visitGetExpr(self, expr):
        self.resolve(expr.object)

    def visitSetExpr(self, expr):
        self.resolve(expr.value)
        self.resolve(expr.object)

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
        if expr.step is not None:
            self.resolve(expr.step)

    def visitGroupingExpr(self, expr):
        self.resolve(expr.expr)

    def visitLiteralExpr(self, expr):
        pass
