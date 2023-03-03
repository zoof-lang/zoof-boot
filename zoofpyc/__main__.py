import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from zoofpyc import ZoofCompiler

foo = 3

if __name__ == "__main__":
    ZoofCompiler().main()
