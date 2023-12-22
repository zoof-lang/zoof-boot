"""
Little script to run from my IDE for rapid proototyping.
"""

import zoofc1
from zoofc1 import main, Source, ZoofCompiler, tree

# main(["example.zf"])
# main([])

c = ZoofCompiler()
m = c.createModule("main")


source = """
struct Vector
    x F64
    y F64


impl Vector

    func new(x, y) do
        return This(x, y)

    getter x() its this..x
    setter x(v) do
        this..x = v

    getter y() its this..y
    setter y(v) do
        this..y = v

    getter length() do
        return (this..x^2 + this..y^2) ^ 0.5


v = Vector.new(1, 2)
print v
print v.x
print v.y
print v.length

v.x = 3
print v.x
print v.length


"""

s1 = Source("i1", 1, source)

m.execute(s1)
# m.execute(s2)
# m.executePartial(s3)
