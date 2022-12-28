#!/usr/bin/pypy3

from PIL import Image
import struct
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Provide a file to unpack")
        exit()
    image_path_str = sys.argv[1]
    image_path = Path(image_path_str)
    image_size = (1024, 768)
    image_data = b""
    image = Image.new("RGB", image_size)
    with image_path.open(mode="rb") as infile:
        position = 1
        while True:
            rawlen = infile.read(2)
            if len(rawlen) == 0:
                break
            (length,) = struct.unpack(">H", rawlen)
            length &= 0x7fff
            if length == 0:
                break
            row = infile.read(length-2)
            print(f"0x{position:06x} {length}")
            position += length
            if len(row) == 0:
                break
            image_data += row + (b"\0" * (image_size[0]*3 - len(row)))
    image.frombytes(image_data)
    image.save("out.png")
