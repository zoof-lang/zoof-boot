class PrinterVisitor:
    def print(self, expr):
        print(expr.accept(self))

    def parenthesize(self, name, *expressions):
        s = "(" + name + " "
        subs = [expr.accept(self) for expr in expressions]
        s += " ".join(subs)
        s += ")"
        return s

    def visitBinaryExpr(self, expr):
        return self.parenthesize(expr.op.lexeme, expr.left, expr.right)

    def visitGroupingExpr(self, expr):
        return self.parenthesize("group", expr.expr)

    def visitLiteralExpr(self, expr):
        return expr.token.lexeme

    def visitUnaryExpr(self, expr):
        return self.parenthesize(expr.op.lexeme, expr.right)


if __name__ == "__main__":
    from zoofc1 import lexer
    from zoofc1 import tree

    expr = tree.BinaryExpr(
        tree.UnaryExpr(
            lexer.Token(lexer.TT.Minus, "-", 1, 1),
            tree.LiteralExpr(lexer.Token(lexer.TT.LiteralNumber, "123", 1, 1)),
        ),
        lexer.Token(lexer.TT.Star, "*", 1, 1),
        tree.GroupingExpr(
            tree.LiteralExpr(lexer.Token(lexer.TT.LiteralNumber, "45.67", 1, 1))
        ),
    )

    p = PrinterVisitor()
    p.print(expr)
