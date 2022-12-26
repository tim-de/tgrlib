#!/usr/bin/pypy3

from pathlib import Path
import sys

import ifflib


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Please enter a file to load")
        exit()
        
    f = ifflib.iff_file()

    f.load(sys.argv[1])
    d = f.data
    print(d.type)
    print(d.length)

    fname = Path(sys.argv[1])
    
    writedir = Path(fname.stem + '_' + fname.suffix[1:])
    writedir.mkdir(mode=0o777, parents=True, exist_ok=True)
    
    for index, chunk in enumerate(d.data):
        writepath = writedir / f"{index}_{chunk.type}"
        with writepath.open("wb") as out_fh:
            out_fh.write(chunk.data)
