#!/usr/bin/pypy3

import ifflib
import struct
import io
import sys
import typing
from dataclasses import dataclass
from pathlib import Path
from PIL import Image

verbose = True

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
    
    def to_int(self):
        r5 = round(self.red / 255 * 31)
        g6 = round(self.green / 255 * 63)
        b5 = round(self.blue / 255 * 31)
        a5 = round(self.alpha / 255 * 31)
        
        return (r5, g6, b5, a5)

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

def load_player_colors(path: str = 'COLORS.INI'):
    path = Path(path)
    player_cols = {}
    if path.is_file():
        with open(path, "r") as fh:
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
    # Backup blue player colors if file doesn't load
    else:
        player_cols[2] = [
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

player_cols = load_player_colors()


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
        _ = sprite
        header_offset = in_fh.tell()
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
            #if newline.data_length == 0:
            #    continue
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
                
    def __init__(self, filename: str, read_from: str, is_sprite=False):
        self.filename = filename
        self.read_from = read_from
        match self.read_from:
            case 'TGR':
                self.iff = ifflib.iff_file(self.filename)
            case 'PNG':
                self.img = Image.open(self.filename)
            case _:
                print(f"Error: invalid read type {self.read_from}")
                
        self.size: typing.Tuple[int, int] = (0,0)
        self.is_sprite = is_sprite
        self.framesizes = []
        self.frameoffsets = []
        self.frames = []

    def load(self):
        match self.read_from:
            case 'TGR':
                self.iff.load()
                if self.iff.data.formtype != "TGAR":
                    print(f"Error: invalid file type: {self.iff.data.formtype}")
                self.read_header()
                if self.indexed_colour:
                    self.load_palette()
                self.get_frames()
            case 'PNG':
                self.img_data = self.img.getdata()
                self.size = self.img.size
                
                

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
            (count,) = struct.unpack("<Hxx", in_fh.read(4))
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

    def extractLine(self, fh: io.BufferedReader, frame_index=0, line_index=0, increment=0, color=2):
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
                    alpha_raw = fh.read(1)[0] & 31
                    alpha = round((alpha_raw / 31) * 255)
                    #alpha = round(int.from_bytes(fh.read(1),byteorder=sys.byteorder) / 31 * 255) & 255# convert alpha channel from 5 bits to 8 bits
                    line_ix +=1
                    #print(f"alpha: {alpha}")
                    # TODO use intensity to set luminosity of pixels
                    pixel = self.get_next_pixel(fh)
                    pixel.alpha = alpha
                    outbuf += [pixel for _ in range(run_length+increment)]
                    pixel_ix += run_length+increment
                    line_ix += self.bits_per_px // 8
                case 0b100:
                    pixel = self.get_next_pixel(fh)
                    pixel.alpha = round(run_length / 31 * 255)
                    outbuf.append(pixel)
                    line_ix += self.bits_per_px // 8
                    pixel_ix += 1
                case 0b101:
                    #outbuf.append(Pixel(0xff, 0x00, 0xff))
                    outbuf += [shadow for _ in range(run_length + increment)]
                case 0b110:
                    #print(f"flag 6 at 0x{fh.tell()-1:08x}")
                    outbuf.append(player_cols[color][run_length])
                    pixel_ix += 1
                case 0b111:
                    read_length = (run_length + 1) // 2
                    color_index = fh.read(read_length)
                    line_ix += read_length
                    
                    for i, b in enumerate(color_index):
                        # splits the byte into two 4bit sections, shifts left 1bit, and sets least sig to 1
                        # then uses as index for player color value
                        outbuf.append(player_cols[color][((b >> 3) & 0b11111) | 0b1])
                        pixel_ix += 1
                        # Don't append trailing null padding on odd run lengths
                        if (run_length % 2 == 0) or (i < len(color_index) - 1):
                            outbuf.append(player_cols[color][((b << 1) & 0b11111) | 0b1])
                            pixel_ix += 1                    
                case _:
                    print(f"{line_index:3d},{pixel_ix:3d}: Unsupported flag {flag} in datapoint 0x{run_header[0]:02x} at offset 0x{fh.tell()-1:08x}")
        if len(outbuf) < line.pixel_length:
            print(f"Appending {line.pixel_length - len(outbuf)} pixels to line {line_index}")
            outbuf += [transparency for _ in range(line.pixel_length - len(outbuf))]
        return outbuf
    
    def look_ahead(self, p: Pixel, line_index, pixel_ix, matching=True):
        collected = 0
        if matching:
            while p == Pixel(*self.img_data[line_index*self.size[0] + pixel_ix + 1 + collected]):
                collected += 1
                if collected == 30:
                    break
            return collected
        else:
            while Pixel(*self.img_data[line_index*self.size[0] + pixel_ix + collected]) != Pixel(*self.img_data[line_index*self.size[0] + pixel_ix + collected + 1]) and Pixel(*self.img_data[line_index*self.size[0] + pixel_ix + collected]).alpha == 255:
                print(f"    Look_Ahead: pixel {Pixel(*self.img_data[line_index*self.size[0] + pixel_ix + collected])} at c:{pixel_ix + collected} doesn't match pixel {Pixel(*self.img_data[line_index*self.size[0] + pixel_ix + collected + 1])} at c:{pixel_ix + collected + 1}")
                collected += 1
                if collected == 31:
                    break
            return collected
        
    
    def encodeLine(self, line_index=0):
        out_fh = open('outfile.tgr','wb')
        if verbose:
            print(f"image size:{self.size}")
        pixel_ix = 0
        
        while pixel_ix < self.size[0]:
            
            p = Pixel(*self.img_data[line_index*self.size[0] + pixel_ix])
            if verbose:
                print(f'reading p:{p} at l:{line_index} c:{pixel_ix}')

            if p.alpha == 0:        # Encode transparent pixels
                if verbose:
                    print(f'  chose flag 0b000')
                flag = 0b000 << 5
                run_length = self.look_ahead(p, line_index, pixel_ix) + 1
                header = flag + (run_length & 0b11111)
                out_fh.write(struct.pack('<B', header))
                pixel_ix += run_length
                if verbose:
                    print(f'  packing header {header:02X}\n  advanced to c:{pixel_ix}')
                
            elif p.alpha < 255:     #Encode translucent pixels                    
                run_length = self.look_ahead(p, line_index, pixel_ix) + 1
                (r,g,b,a) = p.to_int()
                if run_length == 1:
                    if verbose:
                        print(f'  chose flag 0b100')
                    flag = 0b100 << 5
                    header = flag + (a & 0b11111)
                    body = (r << 11) + (g << 5) + b
                    if verbose:
                        print(f"  packing header {header:02X} and body {body:04X}")
                    out_fh.write(struct.pack('<BH', header, body))
                else:
                    if verbose:
                        print(f'  chose flag 0b011')
                    flag = 0b011 << 5
                    header = flag + (run_length & 0b11111)
                    body = (r << 11) + (g << 5) + b
                    out_fh.write(struct.pack('<BBH', header, a, body))
                    if verbose:
                        print(f'  packing header {header:02X} alpha {a:02X} and body {body:04X}')
                pixel_ix += run_length
                if verbose:
                    print(f'  advanced to c:{pixel_ix}')
                
            else:                   # Encode opaque pixels
                matching = self.look_ahead(p, line_index, pixel_ix)
                if matching:
                    if verbose:
                        print(f'  chose flag 0b001')
                    flag = 0b001 << 5
                    run_length = matching + 1
                    header = flag + (run_length & 0b11111)
                    (r,g,b,a) = p.to_int()
                    body = (r << 11) + (g << 5) + b
                    out_fh.write(struct.pack('<BH', header, body))
                    pixel_ix += run_length
                    if verbose:
                        print(f'  packing header {header:02X} and body {body:04X}\n  advanced to c:{pixel_ix}')
                else:
                    if verbose:
                        print(f'  chose flag 0b010')
                    run_length = self.look_ahead(p, line_index, pixel_ix, matching=False)
                    if verbose:
                        print(f'  found {run_length} unique pixels')
                    flag = 0b010 << 5
                    header = flag + (run_length & 0b11111)
                    out_fh.write(struct.pack('<B', header))
                    if verbose:
                        print(f'  packing header {header:02X}')
                    for i in range(pixel_ix,pixel_ix+run_length):
                        (r,g,b,a) = Pixel(*self.img_data[line_index*self.size[0] + pixel_ix + i]).to_int()
                        if verbose:
                            print(f'    r:{r} g:{g} b:{b} a:{a}')
                        body = (r << 11) + (g << 5) + b
                        out_fh.write(struct.pack('<H', body))
                        if verbose:
                            print(f'    packing body:{body:04X}')
                    pixel_ix += run_length
                    if verbose:
                        print(f'  advanced to c:{pixel_ix}')
                    
                    
            # Read pixels
            # If pixel has alpha value, check if transparent count how many pixels have identical values, then encode run of 0b100 if 1, or 0b011 if 2+
            
        out_fh.close()
        
if __name__ == "__main__":
    pass
