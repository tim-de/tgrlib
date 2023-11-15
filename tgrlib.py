#!/usr/bin/pypy3

import ifflib
import struct
import io
from dataclasses import dataclass

def read_line_length(in_fh: io.BufferedReader):
    rawlen = in_fh.read(2)
    if len(rawlen) < 2:
        return 0
    if rawlen[0] & 0x80 != 0:
        (length,) = struct.unpack(">H", rawlen)
        return length & 0x7fff
    else:
        in_fh.seek(-1, 1)
        return rawlen[0]

def get_sprite_line_info(in_fh: io.BufferedReader):
    data = in_fh.read(3)
    if len(data) < 3:
        return {"data_length": 0}
    return {"data_length": data[0],
            "start": data[1],
            "pixel_length": data[2]}

def getRunData(byte):
    flag = byte >> 5
    length = byte & 31
    return (flag, length)

@dataclass
class Pixel:
    """Class for managing pixel values in different formats"""
    red: int
    green: int
    blue: int
    alpha: int = 0xff

    @classmethod
    def from_int(cls, half_word: int):
        # Shift values move each colour channel to the right
        # place value.
        # Bitwise AND masks off the unwanted bits to leave
        # only the desired channel.
        blue = (half_word << 3) & 0xff
        green = (half_word >> 3) & 0xfc
        red = (half_word >> 8) & 0xf8
        return cls(red, green, blue)

    def pack_to_bin(self, format: str ="RGB"):
        if format == "RGB":
            return struct.pack("BBB", self.red, self.green, self.blue)
        elif format == "RGBA":
            return struct.pack("BBBB", self.red, self.green, self.blue, self.alpha)
        else:
            raise Exception("Invalid pixel format specifier")

transparency = Pixel(0x00, 0xff, 0xff, 0x00)

def packPixel(value=(0,0,0), alpha=False):
    if len(value) < 3:
        raise ValueError("Not enough pixel data")
    if alpha:
        if len(value) == 3:
            return struct.pack("BBBB", value[0], value[1], value[2], 0xff)
        return struct.pack("BBBB", value[0], value[1], value[2], value[3])
    return struct.pack("BBB", value[0], value[1], value[2])

def decodePixel(half_word: int):
    # Shift values move each colour channel to the right
    # place value.
    # Bitwise AND masks off the unwanted bits to leave
    # only the desired channel.
    blue = (half_word << 3) & 0xff
    green = (half_word >> 3) & 0xfc
    red = (half_word >> 8) & 0xf8
    return Pixel(red, green, blue)

class Line:
    def __init__(self, in_fh: io.BufferedReader, sprite=False):
        header_offset = in_fh.tell()
        if sprite:
            # print("Fetching sprite line data")
            data = in_fh.read(3)
            if len(data) < 3:
                self.data_length = 0
                self.transparent_pixels = 0
                self.pixel_length = 0
                return
            else:
                total_length = data[0]
                self.transparent_pixels = data[1]
                self.pixel_length = data[2]
        else:
            total_length = read_line_length(in_fh)
            self.transparent_pixels = read_line_length(in_fh)
            self.pixel_length = read_line_length(in_fh)
        self.offset = in_fh.tell()
        self.data_length = total_length - (self.offset - header_offset)
                
class Frame:
    def __init__(self, size, in_fh: io.BufferedReader):
        self.size = size
        self.lines = []
        while True:
            newline = Line(in_fh, False)
            if newline.data_length == 0:
                break
            self.lines.append(newline)
            if len(self.lines) >= self.size[1]:
                break
            in_fh.seek(newline.offset + newline.data_length)

class tgrFile:
    """
    A class representing a .TGR game asset file,
    which as a format is based on the IFF file structure
    """
        # TODO: add methods for decoding a frame into either a list of bytes
        #       or a PIL image (but might be best to keep it light on dependencies)
                
    def __init__(self, filename: str, is_sprite=False):
        self.filename = filename
        self.iff = ifflib.iff_file(self.filename)
        self.size = None
        self.is_sprite = is_sprite
        self.framesizes = []
        self.frames = []

    def load(self):
        self.iff.load()
        if self.iff.data.formtype != "TGAR":
            print(f"Error: invalid file type: {self.iff.data.formtype}")
        self.read_header()
        if self.indexed_colour:
            self.load_palette()
        self.get_frames()

    def read_header(self):
        with open(self.filename, "rb") as in_fh:
            in_fh.seek(self.iff.data.children[0].data_offset)
            (self.version,
             self.framecount,
             self.bits_per_px) = struct.unpack("IHBx", in_fh.read(8))
            (index_mode,
             self.offset_flag) = struct.unpack("xBBx", in_fh.read(4))
            self.size = struct.unpack("HH", in_fh.read(4))
            self.hotspot = struct.unpack("HH", in_fh.read(4))
            
            #print(self.offset_flag)
            self.indexed_colour = index_mode & 0x7f == 0x1a
            in_fh.seek(20, 1)
            #if self.indexed_colour:
            #    in_fh.seek(12, 1)
            for _ in range(self.framecount):
                (ulx, uly, lrx, lry, offset) = struct.unpack("HHHHI", in_fh.read(12))
                #in_fh.seek(4, 1)
                #self.framesizes.append(struct.unpack("HH", in_fh.read(4)))
                self.framesizes.append((1+lrx-ulx, 1+lry-uly, offset))
        #print(len(self.framesizes))

    def load_palette(self):
        palt = self.iff.data.children[1]
        self.palette = []
        with open(self.filename, "rb") as in_fh:
            in_fh.seek(palt.data_offset)
            (count,) = struct.unpack("<I", in_fh.read(4))
            print(count)
            for _ in range(count):
                raw_pixel = in_fh.read(2)
                if len(raw_pixel) < 2:
                    raise ValueError("Not enough image data")
                (pixel,) = struct.unpack("H", raw_pixel)
                self.palette.append(Pixel.from_int(pixel))
        #print(len(self.palette))
    
    def get_frames(self):
        with open(self.filename, "rb") as in_fh:
            for child in self.framesizes:
                in_fh.seek(child[2])
                newframe = Frame((child[0], child[1]), in_fh)
                self.frames.append(newframe)

    def get_next_pixel(self, in_fh: io.BufferedReader):
        if self.indexed_colour:
            (pixel_ix,) = struct.unpack("B", in_fh.read(1))
            return self.palette[pixel_ix-1]
        else:
            (raw_pixel,) = struct.unpack("H", in_fh.read(2))
            return Pixel.from_int(raw_pixel)

    def extractLine(self, fh: io.BufferedReader, frame_index=0, line_index=0, increment=0):
        outbuf = []
        line_ix = 0
        pixel_ix = 0
        line = self.frames[frame_index].lines[line_index]
        fh.seek(line.offset)
        # print(f"Extracting line of length 0x{line.pixel_length:x}")
        for _ in range(line.transparent_pixels):
            outbuf.append(transparency)
        pixel_ix += line.transparent_pixels
        
        while line_ix < line.data_length:# and pixel_ix < line.pixel_length:
            run_header = fh.read(1)
            line_ix += 1
            (flag, run_length) = getRunData(run_header[0])
            match flag:
                case 0b000:
                    outbuf += [transparency for _ in range(run_length + increment)]
                case 0b001:
                    pixel = self.get_next_pixel(fh)
                    outbuf += [pixel for _ in range(run_length+increment)]
                    pixel_ix += run_length+increment
                    line_ix += self.bits_per_px // 8
                case 0b010:
                    for _ in range(run_length+increment):
                        outbuf.append(self.get_next_pixel(fh))
                        line_ix += self.bits_per_px // 8
                        pixel_ix += 1
                case 0b011:
                    outbuf.append(Pixel(0x0, 0xff, 0xff))
                    #outbuf += [Pixel(0x0, 0xff, 0xff) for _ in range(run_length + increment)]
                case 0b100:
                    outbuf += [Pixel(0xff, 0x0, 0x0) for _ in range(run_length + increment)]
                case 0b101:
                    outbuf += [Pixel(0xff, 0, 0xff) for _ in range(run_length + increment)]
                case 0b110:
                    outbuf.append(Pixel(8*run_length, 0, 0))
                    line_ix += 1
                    pixel_ix += 1
                case 0b111:
                    for _ in range(run_length+increment):
                        outbuf.append(Pixel(0x55, 0xff, 0x55))
                        pixel_ix += 1
                    fh.seek((run_length + 1) // 2, 1)
                    line_ix += ((run_length + 1) // 2) + 1
                case _:
                    print(f"{line_index:3d},{pixel_ix:3d}: Unsupported flag {flag} in datapoint 0x{run_header[0]:02x} at offset 0x{fh.tell()-1:08x}")
        if len(outbuf) < line.pixel_length:
            print(f"Appending {line.pixel_length - len(outbuf)} pixels to line {line_index}")
            outbuf += [transparency for _ in range(line.pixel_length - len(outbuf))]
        return outbuf 
if __name__ == "__main__":
    pass
