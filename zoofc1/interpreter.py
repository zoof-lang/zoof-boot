import time

from .tokens import TT, Token


## Minilib


class ZoofRange:
    def __init__(self, start, stop, step=1):
        self.start = start
        self.stop = stop
        if step is None:
            step = 1
        assert step > 0
        self.step = step


class Callable:
    def arity(self):
        raise NotImplementedError()

    def call(self, interpreter, arguments):
        raise NotImplementedError()


class NativeCallable(Callable):
    pass


class Clock(NativeCallable):
    def arity(self):
        return 0

    def call(self, interpreter, arguments):
        return time.perf_counter()


class ArbitraryNumber(NativeCallable):
    def arity(self):
        return 0

    def call(self, interpreter, arguments):
        return 7.0  # not random, arbitrary! (consistent for tests)


class ZoofFunction(Callable):
    def __init__(self, declaration, closure, bindings, source):
        self.declaration = declaration
        self.closure = closure
        self.bindings = bindings
        self.source = source
        self.freeVars = self.declaration.freeVars.copy()
        self.captured = {}

    def arity(self):
        return len(self.declaration.params)

    def popEnvironment(self, environment):
        # This is where we would capture the free variables, if we were
        # to support closures.
        toPop = set()
        for name, expr in self.freeVars.items():
            if name in environment.map:
                toPop.add(name)
                self.captured[name] = expr
        for name in toPop:
            self.freeVars.pop(name)
        # Be good for memory
        environment.map.clear()

    def call(self, interpreter, arguments, bindings=None):
        if self.captured:
            expr = list(self.captured.values())[0]
            raise RuntimeErr(
                "E8135",
                "Closures are not supported at the moment.",
                expr.name,
            )
        environment = Environment(self.closure)
        # for name, value in self.captured.items():
        #     environment.set(name, value)
        for name, ob in self.bindings.items():
            environment.set(name, ob)
        for name, ob in (bindings or {}).items():
            environment.set(name, ob)
        for param, arg in zip(self.declaration.params, arguments):
            environment.set(param, arg)

        prevSource = interpreter.ehandler.swapSource(self.source)
        try:
            if isinstance(self.declaration.body, list):
                # Declaration function
                try:
                    interpreter.executeBlock(self.declaration.body, environment)
                except Return as ret:
                    return ret.value
                else:
                    return None
            else:
                # A lambda / expression function
                return interpreter.executeBlock(self.declaration.body, environment)
        finally:
            interpreter.ehandler.swapSource(prevSource)

    def bind(self, new_bindings):
        bindings = self.bindings.copy()
        bindings.update(new_bindings)
        return ZoofFunction(self.declaration, self.closure, bindings, self.source)


class ZoofStruct:
    def __init__(self, declaration, closure, source):
        self.declaration = declaration
        closure  # is not used (for now?)
        self.source = source

        self.funcs = {}
        self.methods = {}
        self.getters = {}
        self.setters = {}

    def addFunction(self, fn):
        name = fn.declaration.name.lexeme
        kind = fn.declaration.token.lexeme
        if kind == "func":
            self.funcs[name] = fn
        elif kind == "getter":
            self.getters[name] = fn
        elif kind == "setter":
            self.setters[name] = fn
        elif kind == "method":
            self.methods[name] = fn
        else:
            raise RuntimeError(f"Unforesoon function kind '{kind}'.")

    def get(self, nameToken):
        name = nameToken.lexeme
        fn = self.funcs.get(name, None)
        if fn is not None:
            return fn
        else:
            raise RuntimeErr(
                "E8000",
                f"Struct {self.declaration.name} does not have static function '{name}'.",
                nameToken,
                "",
            )

    def instantiate(self, arguments):
        names = list(self.declaration.fields.keys())
        assert len(arguments) == len(names)
        data = {}
        for name, value in zip(names, arguments):
            data[name] = value
        return ZoofInstance(self, data)

    # def arity(self):
    #     if self.constructor:
    #         return self.constructor.arity()
    #     return 0
    #
    # def call(self, interpreter, arguments):
    #     if self.constructor:
    #         # return self.constructor.call(interpreter, arguments)
    #         return ZoofInstance(self)
    #     else:
    #         raise RuntimeErr(
    #             "E8000",
    #             f"Struct {self.declaration.name} does not have a 'new()' method.",
    #             self.declaration.token,
    #             "To instantiate (i.e. call) a struct object, it must have a method called 'new'.",
    #             )


class ZoofInstance:
    def __init__(self, archetype, data):
        self.archetype = archetype
        self.data = data

    def getData(self, nameToken):
        name = nameToken.lexeme
        if name not in self.data:
            structName = self.archetype.declaration.name.lexeme
            raise RuntimeErr(
                "E8000",
                f"Struct {structName} does not have a field '{name}' to get.",
                nameToken,
                "",
            )
        return self.data[name]

    def setData(self, nameToken, value):
        name = nameToken.lexeme
        if name not in self.data:
            structName = self.archetype.declaration.name.lexeme
            raise RuntimeErr(
                "E8000",
                f"Struct {structName} does not have a field'{name}' so set.",
                nameToken,
                "",
            )
        self.data[name] = value

    def getProp(self, interpreter, nameToken):
        name = nameToken.lexeme
        fn = self.archetype.getters.get(name, None)
        bindings = {"self": self}
        if fn is not None:
            attr = fn.call(interpreter, [], bindings)
        else:
            fn = self.archetype.methods.get(name, None)
            if fn is not None:
                attr = fn.bind(bindings)
            else:
                structName = self.archetype.declaration.name.lexeme
                raise RuntimeErr(
                    "E8000",
                    f"Struct {structName} does not have a getter or method called '{name}'.",
                    nameToken,
                    "",
                )
        return attr

    def setProp(self, interpreter, nameToken, value):
        name = nameToken.lexeme
        fn = self.archetype.setters.get(name, None)
        if fn is not None:
            bindings = {"self": self}
            fn.call(interpreter, [value], bindings)
        else:
            structName = self.archetype.declaration.name.lexeme
            raise RuntimeErr(
                "E8000",
                f"Struct {structName} does not have a setter called '{name}'.",
                nameToken,
                "",
            )


BUILTINS = {}
BUILTINS["clock"] = Clock()
BUILTINS["arbitraryNumber"] = ArbitraryNumber()

##


class RuntimeErr(Exception):
    def __init__(self, code, message, token, *explanation):
        super().__init__(message)
        self.code = code
        self.message = message
        self.token = token
        self.explanation = "\n".join(explanation)


class Return(Exception):
    def __init__(self, value):
        super().__init__()
        self.value = value


class Break(Exception):
    pass


class Environment:
    def __init__(self, parent):
        self.parent = parent
        self.index = 0 if parent is None else parent.index + 1
        self.map = {}
        self.loopStack = []

    def set(self, name: Token, value):
        if isinstance(name, str):
            self.map[name] = value
        else:
            self.map[name.lexeme] = value

    def get(self, name: Token):
        try:
            return self.map[name.lexeme]
        except KeyError:
            raise RuntimeErr(
                "E8774",
                "Undefined variable.",
                name,
                "This variable name is used before it is defined.",
            )


class InterpreterVisitor:
    def __init__(self, print, ehandler):
        self.print = print
        self.ehandler = ehandler
        builtins = Environment(None)
        builtins.map.update(BUILTINS)
        self.env = Environment(builtins)
        self.maybeClosures = []  # todo: refactor this mechanism

    def interpret(self, program):
        """Interpret the given program."""
        # Init
        self.ehandler.swapSource(program.source)

        try:
            val = None
            for statement in program.statements:
                val = self.execute(statement)
            # Print the last value if it was an expression-statement
            if val is not None:
                self.print(self.stringify(val))
        except RuntimeErr as err:
            self.ehandler.runtimeError(
                err.code, err.message, err.token, err.explanation
            )
        except Exception as err:
            raise err

    def executeBlock(self, body, environment):
        # todo: only really used for functions!
        original_env = self.env
        self.env = environment
        self.maybeClosures.append([])
        try:
            if isinstance(body, list):
                for stmt in body:
                    self.execute(stmt)
            else:
                return self.evaluate(body)
        finally:
            if self.maybeClosures:
                for func in self.maybeClosures.pop(-1):
                    func.popEnvironment(self.env)
            self.env = original_env

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
            raise RuntimeErr(
                "E8295",
                f"Cannot convert {typename} to bool.",
                token,
                "Zoof does not support implicit truethyness. You need to do an explicit",
                "check that resolves to a boolean.",
            )

    def checkNumberOperand(self, op, right):
        if not isinstance(right, float):
            classname = right.__class__.__name__
            raise RuntimeErr(
                "E8875",
                f"Unary operand must be a number, not '{classname}'.",
                op,
            )

    def checkNumberOperands(self, op, left, right):
        if not isinstance(left, float):
            classname = left.__class__.__name__
            raise RuntimeErr(
                "E8334",
                f"Left operand must be a number, not '{classname}'.",
                op,
            )
        if not isinstance(right, float):
            classname = right.__class__.__name__
            raise RuntimeErr(
                "E8410",
                f"Right operand must be a number, not '{classname}'.",
                op,
            )

    def isEqual(self, left, right):
        if left is None and right is None:
            return True
        else:
            return left == right

    def stringify(self, value):
        if value is None:
            return "nil"
        elif isinstance(value, bool):
            return "true" if value else "false"
        else:
            return repr(value)

    # %%

    def visitDoStmt(self, stmt):
        self.exececuteMultiple(stmt.statements)

    def visitIfStmt(self, stmt):
        if self.isTruethy(self.evaluate(stmt.condition), stmt.condition):
            self.exececuteMultiple(stmt.thenBranch)
        else:
            self.exececuteMultiple(stmt.elseBranch)

    def visitWhileStmt(self, stmt):
        self.env.loopStack.append(True)
        try:
            while self.isTruethy(self.evaluate(stmt.condition), stmt.condition):
                self.exececuteMultiple(stmt.statements)
        except Break:
            pass
        self.env.loopStack.pop(-1)

    def visitForStmt(self, stmt):
        iter = self.evaluate(stmt.iter)
        assert isinstance(iter, ZoofRange)
        value = iter.start
        self.env.loopStack.append(True)
        try:
            while value < iter.stop:
                self.env.set(stmt.var.name, value)
                self.exececuteMultiple(stmt.statements)
                value += iter.step
        except Break:
            pass
        self.env.loopStack.pop(-1)

    def visitBreakStmt(self, stmt):
        if not self.env.loopStack:
            raise RuntimeErr(
                "E8311",
                "Can only use break inside a for-loop or while-loop.",
                stmt.token,
            )
        else:
            raise Break()

    def visitPrintStmt(self, stmt):
        value = self.evaluate(stmt.expr)
        self.print(self.stringify(value))

    def visitReturnStmt(self, stmt):
        if stmt.value is None:
            value = None
        else:
            value = self.evaluate(stmt.value)
        raise Return(value)

    def visitFunctionStmt(self, stmt):
        function = ZoofFunction(stmt, self.env, {}, self.ehandler.source)
        self.env.set(stmt.name, function)
        if self.maybeClosures:
            self.maybeClosures[-1].append(function)

    def visitStructStmt(self, stmt):
        struct = ZoofStruct(stmt, self.env, self.ehandler.source)
        self.env.set(stmt.name, struct)

    def visitImplStmt(self, stmt):
        ob = self.env.get(stmt.target)
        if isinstance(ob, ZoofStruct):
            for funcStmt in stmt.functions:
                fn = ZoofFunction(
                    funcStmt, self.env, {"Self": ob}, self.ehandler.source
                )
                ob.addFunction(fn)
                if self.maybeClosures:
                    self.maybeClosures[-1].append(function)
        else:
            raise RuntimeErr(
                "E8000",
                f"Cannot impl '{stmt.target.lexeme}' because it is not a Struct or Trait.",
                stmt.target,
            )

    def visitExpressionStmt(self, stmt):
        return self.evaluate(stmt.expr)

    # %%

    def visitVariableExpr(self, expr):
        env = self.env
        assert expr.depth >= 0
        while env.index > 0 and env.index > expr.depth:
            env = env.parent
        return env.get(expr.name)

    def visitGetExpr(self, expr):
        ob = self.evaluate(expr.object)
        if isinstance(ob, ZoofStruct):
            return ob.get(expr.name)
        elif isinstance(ob, ZoofInstance):
            if expr.token.lexeme == "..":
                # todo: only allow in methods
                return ob.getData(expr.name)
            else:
                return ob.getProp(self, expr.name)
        else:
            raise RuntimeErr(
                "E8000",
                "Cannot use getter on this object. Not a struct.",
                expr.object,
            )

    def visitSetExpr(self, expr):
        ob = self.evaluate(expr.object)
        if isinstance(ob, ZoofInstance):
            value = self.evaluate(expr.value)
            if expr.token.lexeme == "..":
                # todo: only allow in methods
                ob.setData(expr.name, value)
            else:
                ob.setProp(self, expr.name, value)
            return value
        else:
            raise RuntimeErr(
                "E8000",
                "Cannot use getter on this object. Not a struct.",
                expr.object,
            )

    def visitIfExpr(self, expr):
        if self.isTruethy(self.evaluate(expr.condition), expr.condition):
            return self.evaluate(expr.thenExpr)
        else:
            return self.evaluate(expr.elseExpr)

    def visitFunctionExpr(self, expr):
        function = ZoofFunction(expr, self.env, {}, self.ehandler.source)
        if self.maybeClosures:
            self.maybeClosures[-1].append(function)
        return function

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
            None if expr.step is None else self.evaluate(expr.step),
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
            raise RuntimeErr(
                "E8821",
                f"Unexpected literal: '{expr.token.lexeme}'.",
                expr.token,
            )

    def visitUnaryExpr(self, expr):
        right = self.evaluate(expr.right)
        if expr.op.type == TT.Minus:
            self.checkNumberOperand(expr.right, right)
            return -right
        if expr.op.type == TT.Plus:
            self.checkNumberOperand(expr.right, right)
            return right
        else:
            raise RuntimeErr(
                "E8259",
                f"Unexpected unary operation.",
                expr.op,
            )

    def visitLogicalExpr(self, expr):
        left = self.evaluate(expr.left)
        opname = expr.op.lexeme
        if opname == "or":
            if self.isTruethy(left, expr.left):
                return left
            return self.evaluate(expr.right)
        elif opname == "and":
            if not self.isTruethy(left, expr.right):
                return left
            return self.evaluate(expr.right)
        else:
            raise RuntimeErr(
                "E8092",
                f"Unexpected logical expression '{optype}'.",
                expr.op,
            )

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
                raise RuntimeErr(
                    "E8255",
                    f"Cannot add '{classname1}' and '{classname2}' objects.",
                    expr.op,
                )
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
            raise RuntimeErr(
                "E8701",
                f"Unexpected binary expression '{optype}'.",
                expr.op,
            )

    def visitCallExpr(self, expr):
        callee = self.evaluate(expr.callee)
        arguments = [self.evaluate(argExpr) for argExpr in expr.arguments]

        if isinstance(callee, ZoofStruct) and callee is self.env.map.get("Self", None):
            return callee.instantiate(arguments)

        # todo: error is bound to the closing paren :/
        if not isinstance(callee, Callable):
            raise RuntimeErr(
                "E8247",
                "Not a callable object.",
                expr,
                "The code attempts to call an object that cannot be called.",
                "Perhaps you thought this was a function, but it's not?",
            )
        elif callee.arity() != len(arguments):
            raise RuntimeErr(
                "E8960",
                f"Callee Expected {callee.arity()} arguments, but the call has {len(arguments)}.",
                expr.paren,
                "The callable object cannot be called this way. You should probably",
                "double-check the signature.",
            )

        return callee.call(self, arguments)
