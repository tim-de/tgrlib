#!/usr/bin/pypy3

import sys
import io
import tgrlib
from PIL import Image
import struct

def getRunData(byte):
    flag = byte >> 5
    length = byte & 31
    return (flag, length)

def decodePixel(half_word: int):
    blue = half_word & 0b11111
    green = (half_word >> 6) & 0b11111
    red = (half_word >> 11) & 0b11111
    return struct.pack("bbb", red << 2, green << 2, blue << 2)

def extractLine(line: tgrlib.tgrFile.frame.line, fh: io.BufferedReader):
    outbuf = b""
    line_ix = 0
    fh.seek(line.offset)
    while line_ix < line.length:
        run_header = fh.read(1)
        line_ix += 1
        (flag, run_length) = getRunData(run_header[0])
        if flag == 1:
            (raw_pixel,) = struct.unpack("H", fh.read(2))
            pixel = decodePixel(raw_pixel)
            outbuf += pixel * run_length
            line_ix += 2
        elif flag == 2:
            for _ in range(run_length):
                (raw_pixel,) = struct.unpack("H", fh.read(2))
                outbuf += decodePixel(raw_pixel)
                line_ix += 2
    return outbuf     

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
            rawline = extractLine(line, in_fh)
            imagedata += rawline
            if len(rawline) < (3 * frame.size[0]):
                imagedata += b"\xff" * ((3*frame.size[0]) - len(rawline))
            print(f"{idx+1:3d}: 0x{line.offset:06x}, {len(rawline)}")
    print(len(imagedata))
    image.frombytes(imagedata)
    image.save("out.png")
