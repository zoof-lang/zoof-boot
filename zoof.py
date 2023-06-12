"""
Little script to run from my IDE for rapid proototyping.
"""

import zoofc1
from zoofc1 import main, Source, ZoofCompiler, tree

# main(["example.zf"])
# main([])

c = ZoofCompiler()
m = c.createModule("main")

s1 = Source("i1", 1, "and")
# s1 = Source("i1", 1, "  print 3 + 4\n  print 42\n3")
# s2 = Source("i2", 3, "b = 2")
# s3 = Source("i3", 4, "foo()")

m.execute(s1)
# m.execute(s2)
# m.executePartial(s3)
