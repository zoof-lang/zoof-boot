import os
import sys

this_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.split(this_dir)[0])

import zoofc1


if __name__ == "__main__":
    argv = sys.argv.copy()
    if argv and argv[0] == "zoofc1":
        argv.pop(0)

    zoofc1.main(argv)
