#!/usr/bin/pypy3

import ifflib
import struct
import io

class tgrFile:
    """
    A class representing a .TGR game asset file,
    which as a format is based on the IFF file structure
    """
    
    class frame:
        class line:
            def __init__(self, offset, length):
                self.length = length
                self.offset = offset
            def get(self, in_fh: io.BufferedReader):
                in_fh.seek(self.offset)
                return in_fh.read(self.length)
            #def get(self, filename: str):
            #    with open(filename, "rb") as in_fh:
            #        return self.get(in_fh)

        def __init__(self, size, in_fh: io.BufferedReader):
            self.size = size
            self.lines = []
            while True:
                rawlen = in_fh.read(2)
                if len(rawlen) < 2:
                    break
                (length,) = struct.unpack(">H", rawlen)
                
                if length & 0x8000 != 0:
                    length &= 0x7fff
                    datastart = in_fh.tell()+3
                    datalength = length - 5
                else:
                    datastart = in_fh.tell()+1
                    datalength = (length // 256) - 3
                if length == 0 or len(self.lines) >= self.size[1]:
                    break
                self.lines.append(tgrFile.frame.line(datastart, datalength))
                in_fh.seek(datastart + datalength)

        # TODO: add methods for decoding a frame into either a list of bytes
        #       or a PIL image (but might be best to keep it light on dependencies)
                
    def __init__(self, filename: str):
        self.filename = filename
        self.iff = ifflib.iff_file(self.filename)
        self.size = None
        self.framesizes = []
        self.frames = []

    def load(self):
        self.iff.load()
        if self.iff.data.formtype != "TGAR":
            print(f"Error: invalid file type: {self.iff.data.formtype}")
        self.read_header()
        self.get_frames()

    def read_header(self):
        with open(self.filename, "rb") as in_fh:
            in_fh.seek(self.iff.data.children[0].data_offset)
            in_fh.seek(4, 1)
            (self.framecount,) = struct.unpack("H", in_fh.read(2))
            in_fh.seek(6, 1)
            self.size = struct.unpack("HH", in_fh.read(4))
            in_fh.seek(24, 1)
            for _ in range(self.framecount):
                (ulx, uly, lrx, lry, offset) = struct.unpack("HHHHI", in_fh.read(12))
                #in_fh.seek(4, 1)
                #self.framesizes.append(struct.unpack("HH", in_fh.read(4)))
                self.framesizes.append((1+lrx-ulx, 1+lry-uly, offset))
        print(len(self.framesizes))

    def get_frames(self):
        with open(self.filename, "rb") as in_fh:
            for index, child in enumerate(self.framesizes):
                print(index)
                in_fh.seek(child[2])
                frame = tgrFile.frame((child[0], child[1]), in_fh)
                self.frames.append(frame)

if __name__ == "__main__":
    pass
