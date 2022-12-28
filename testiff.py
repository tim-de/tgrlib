#!/usr/bin/pypy3

from pathlib import Path
import sys

import ifflib


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Please enter a file to load")
        exit()
        
    f = ifflib.iff_file(sys.argv[1])

    f.load()
    d = f.data
    print(d.type)
    print(d.length)

    f.dump()
