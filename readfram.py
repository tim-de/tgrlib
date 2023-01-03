#!/usr/bin/pypy3

import sys
import tgrlib
from PIL import Image

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Provide a file to unpack")
        exit()
    image_path = sys.argv[1]

    imagefile = tgrlib.tgrFile(image_path)

    imagefile.load()

    print(imagefile.framecount)
    frame = imagefile.frames[0]
    outfilename = "out.bin"

    min = frame.size[0]
    min_idx = 0
    for index, line in enumerate(frame.lines):
        if line.length < min:
            min = line.length
            min_idx = index

    shortline = frame.lines[min_idx]
    print(f"{min_idx}: 0x{shortline.offset:06x}, {shortline.length}")

    with open(outfilename, "wb") as out_fh:
        with open(imagefile.filename, "rb") as in_fh:
            in_fh.seek(shortline.offset)
            buf = in_fh.read(shortline.length)
            out_fh.write(buf)
    
    image = Image.new("RGB", frame.size)
    imagedata = b""
    with open(image_path, "rb") as in_fh:
        for idx, line in enumerate(frame.lines):
            imagedata += line.get(in_fh)
            imagedata += b"\xff" * ((3*frame.size[0]) - line.length)
            print(f"{idx+1:3d}: 0x{line.offset:06x}, {line.length}")
    print(len(imagedata))
    image.frombytes(imagedata)
    image.save("out.png")
