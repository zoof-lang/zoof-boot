"""
Little script to run from my IDE for rapid proototyping.
"""

import zoofc1  # noqa
from zoofc1 import main, Source, ZoofCompiler, tree  # noqa

# main(["example.zf"])
# main([])

c = ZoofCompiler()
m = c.createModule("main")


source = """
print 42

"""

s1 = Source("i1", 1, source)

m.execute(s1)
# m.execute(s2)
# m.executePartial(s3)
