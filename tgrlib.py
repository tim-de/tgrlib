#!/usr/bin/pypy3

import ifflib
import struct
import io
import typing
from dataclasses import dataclass
from pathlib import Path

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
        
        blue = round((half_word & 0b11111) / 31 * 255)
        green = round(((half_word >> 5) & 0b111111) / 63 * 255)
        red = round(((half_word >> 11) & 0b11111) / 31 * 255)

        return cls(red, green, blue)

    def pack_to_bin(self, format: str ="RGB") -> bytes:
        match format:
            case "RGB":
                return struct.pack("BBB", self.red, self.green, self.blue)
            case "RGBA":
                return struct.pack("BBBB", self.red, self.green, self.blue, self.alpha)
            case _:
                raise Exception("Invalid pixel format specifier")

shadow = Pixel(0, 0, 0, 0x80)
transparency = Pixel(0x00, 0xff, 0xff, 0x00)

def load_player_colors(path: str = '.\COLORS.INI'):
    path = Path(path)
    if path.is_file():
        with open(path+'r', "r") as fh:
            player_cols = {}
            last = fh.seek(0,2)
            fh.seek(0)
            while fh.tell() < last:
                line = "".join(fh.readline().split())
                if line.startswith('Color_'):
                    color = int(line.split('_')[1])
                    channels = [int(c) for c in line.split('=')[1].split(',')]
                    
                    if color in player_cols.keys():
                        player_cols[color].append(Pixel(*channels))
                    else:
                        player_cols[color] = [Pixel(*channels)]
    else:
        player_cols: typing.List[Pixel] = [
        	Pixel(1,4,45),
        	Pixel(1,4,45),
        	Pixel(3,7,51),
        	Pixel(4,11,59),
        	Pixel(6,15,66),
        	Pixel(7,19,74),
        	Pixel(9,23,82),
        	Pixel(10,26,90),
        	Pixel(13,30,97),
        	Pixel(14,34,103),
        	Pixel(15,37,109),
        	Pixel(17,40,114),
        	Pixel(18,44,120),
        	Pixel(20,48,126),
        	Pixel(23,52,132),
        	Pixel(26,57,139),
        	Pixel(30,63,146),
        	Pixel(34,69,153),
        	Pixel(40,78,162),
        	Pixel(48,89,171),
        	Pixel(56,100,180),
        	Pixel(65,111,189),
        	Pixel(74,123,198),
        	Pixel(83,134,206),
        	Pixel(91,144,213),
        	Pixel(98,154,219),
        	Pixel(105,162,225),
        	Pixel(111,170,231),
        	Pixel(117,178,236),
        	Pixel(123,185,241),
        	Pixel(128,191,245),
        	Pixel(132,197,249),
        ]
    return player_cols



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
    blue = round((half_word & 0b11111) / 31 * 255)
    green = round(((half_word >> 5) & 0b111111) / 63 * 255)
    red = round(((half_word >> 11) & 0b11111) / 31 * 255)
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
        self.size: typing.Tuple[int, int] = (0,0)
        self.is_sprite = is_sprite
        self.framesizes = []
        self.frameoffsets = []
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
            print(self.size)
            
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
                self.frameoffsets.append(((ulx, uly), (lrx, lry)))
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
                    outbuf.append(Pixel(0xff, 0x00, 0x00))
                    #outbuf += [Pixel(0xff, 0x0, 0x0) for _ in range(run_length + increment)]
                case 0b101:
                    #outbuf.append(Pixel(0xff, 0x00, 0xff))
                    outbuf += [shadow for _ in range(run_length + increment)]
                case 0b110:
                    #print(f"flag 6 at 0x{fh.tell()-1:08x}")
                    outbuf.append(player_cols[run_length])
                    line_ix += 1
                    pixel_ix += 1
                case 0b111:
                    read_length = (run_length + 1) // 2
                    color_index = fh.read(read_length)
                    line_ix += read_length
                    
                    for i, b in enumerate(color_index):
                        # splits the byte into two 4bit sections, shifts left 1bit, and sets least sig to 1
                        # then uses as index for player color value
                        outbuf.append(player_cols[((b >> 3) & 0b11111) | 0b1])
                        pixel_ix += 1
                        # Don't append trailing null padding on odd run lengths
                        if (run_length % 2 == 0) or (i < len(color_index) - 1):
                            outbuf.append(player_cols[((b << 1) & 0b11111) | 0b1])
                            pixel_ix += 1                    
                case _:
                    print(f"{line_index:3d},{pixel_ix:3d}: Unsupported flag {flag} in datapoint 0x{run_header[0]:02x} at offset 0x{fh.tell()-1:08x}")
        if len(outbuf) < line.pixel_length:
            print(f"Appending {line.pixel_length - len(outbuf)} pixels to line {line_index}")
            outbuf += [transparency for _ in range(line.pixel_length - len(outbuf))]
        return outbuf 
if __name__ == "__main__":
    pass
