#!/usr/bin/pypy3

import sys
import io
import tgrlib
from PIL import Image
from pathlib import Path
import struct

def getRunData(byte):
    flag = byte >> 5
    length = byte & 31
    return (flag, length)

def decodePixel(half_word: int):
    # Shift values move each colour channel to the right
    # place value.
    # Bitwise AND masks off the unwanted bits to leave
    # only the desired channel.
    blue = (half_word << 3) & 0xff
    green = (half_word >> 3) & 0xfc
    red = (half_word >> 8) & 0xf8
    return struct.pack("BBB", red, green, blue)

def extractLine(line: tgrlib.tgrFile.frame.line, fh: io.BufferedReader, line_idx=None):
    outbuf = b""
    line_ix = 0
    pixel_ix = 0
    fh.seek(line.offset)
    #print(f"Extracting line of length 0x{line.length:x}")
    while line_ix < line.data_length:
        run_header = fh.read(1)
        line_ix += 1
        (flag, run_length) = getRunData(run_header[0])
        if flag == 1:
            (raw_pixel,) = struct.unpack("H", fh.read(2))
            pixel = decodePixel(raw_pixel)
            outbuf += pixel * run_length
            pixel_ix += run_length
            line_ix += 2
        elif flag == 2:
            for _ in range(run_length):
                (raw_pixel,) = struct.unpack("H", fh.read(2))
                outbuf += decodePixel(raw_pixel)
                line_ix += 2
                pixel_ix += 1
        elif flag == 6:
            outbuf += struct.pack("BBB", 8*run_length, 0, 0)
            line_ix += 1
            pixel_ix += 1
        elif flag == 7:
            for _ in range(run_length):
                outbuf += struct.pack("BBB", 8, 0, 0)
                pixel_ix += 1
            fh.seek((run_length + 1) // 2, 1)
            line_ix += ((run_length + 1) // 2) + 1
        else:
            print(f"{line_idx:3d},{pixel_ix:3d}: Unsupported flag {flag} in datapoint 0x{run_header[0]:02x} at offset 0x{fh.tell()-1:08x}")
    return outbuf     

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Provide a file to unpack")
        exit()
    image_path = sys.argv[1]

    imagefile = tgrlib.tgrFile(image_path)

    imagefile.load()

    image_name = Path(image_path).stem

    #print(imagefile.framecount)
    frame = imagefile.frames[0]
    #outfilename = "out.bin"

    #min = frame.size[0]
    #min_idx = 0
    #for index, line in enumerate(frame.lines):
    #    if line.length < min:
    #        min = line.length
    #        min_idx = index

    #shortline = frame.lines[min_idx]
    #print(f"{min_idx}: 0x{shortline.offset:06x}, {shortline.length}")

    #with open(outfilename, "wb") as out_fh:
    #    with open(imagefile.filename, "rb") as in_fh:
    #        in_fh.seek(shortline.offset)
    #        buf = in_fh.read(shortline.length)
    #        out_fh.write(buf)
    
    image = Image.new("RGB", frame.size)
    imagedata = b""
    with open(image_path, "rb") as in_fh:
        for idx, line in enumerate(frame.lines):
            rawline = extractLine(line, in_fh, idx)
            imagedata += rawline
            if len(rawline) < (3 * frame.size[0]):
                imagedata += b"\xff" * ((3*line.pixel_length) - len(rawline))
            #print(f"{idx+1:3d}: 0x{line.offset:06x}, {len(rawline)}")
    #print(len(imagedata))
    image.frombytes(imagedata)
    image.save(f"{image_name}.png")
