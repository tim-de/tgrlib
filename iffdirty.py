#!/usr/bin/pypy3

import sys
import os
from pathlib import Path
import struct

def read_iff_chunks(filename):
    in_file = Path(filename)

    with in_file.open(mode="rb") as in_fh:
        position = 0
        buf = in_fh.read(4)
        type = buf.decode("ascii")

        if type != "FORM":
            print("Not a recognised IFF file")
            return

        buf = in_fh.read(4)
        (length,) = struct.unpack(">I", buf)
        buf = in_fh.read(4)
        formtype = buf.decode('ascii')
        print(f"{formtype} :: {length}")
        while position < length:
            buf = in_fh.read(4)
            chunktype = buf.decode('ascii')
            buf = in_fh.read(4)
            (chunklen,) = struct.unpack(">I", buf)
            print(f"{chunktype} => {chunklen}")
            in_fh.seek(chunklen, 1)
            position += 8 + chunklen + (chunklen % 2)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please enter a file to analyse")
        exit()

    read_iff_chunks(sys.argv[1])
