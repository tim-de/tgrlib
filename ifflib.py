#!/usr/bin/pypy3

import struct
import io
from pathlib import Path

class chunk:
    """A basic class for IFF chunks, can implement reading the base
    chunk types of FORM, [LIST, and CAT (not yet implemented)],
    reading child chunk prefixes but not parsing them unless
    parsing of their individual types is implemented separately.
    If the chunk name contains non ascii characters, it returns
    an error."""
    
    def __init__(self):
        self.type = None
        self.data_offset = None
        self.length = None

    def parse(self, in_fh: io.BufferedReader):
        # Read chunk type:
        buf = in_fh.read(4)
        try:
            self.type = buf.decode("ascii")
        except UnicodeDecodeError:
            (val,) = struct.unpack("I", buf)
            return 'Error, invalid data for chunk type: {:08x}'.format(val)

        # Handle known types
        if self.type == "FORM":
            return self.parse_form(in_fh)

        # Handle the general case
        (self.length,) = struct.unpack(">I", in_fh.read(4))
        self.data_offset = in_fh.tell()

        in_fh.seek(self.length, 1)
        return None

    def parse_form(self, in_fh: io.BufferedReader):
        self.children = []
        buf = in_fh.read(4)
        (self.length,) = struct.unpack(">I", buf)
        buf = in_fh.read(4)
        self.formtype = buf.decode('ascii')

        print(self.type, self.length, self.formtype)

        self.data_offset = in_fh.tell()
        
        while in_fh.tell() < self.data_offset + self.length:
            child = chunk()
            errval = child.parse(in_fh)
            if errval != None:
                return errval
            self.children.append(child)
        return None

class iff_file:
    def __init__(self, filename):
        self.data = chunk()
        self.filename = filename

    def load(self):
        in_file = Path(self.filename)
        
        with in_file.open(mode="rb") as in_fh:
            errval = self.data.parse(in_fh)
            if errval != None:
                print(errval)

    def dump(self, outdirname=None):
        filepath = Path(self.filename)
        if outdirname == None:
            writedir = Path(filepath.stem + '_' + filepath.suffix[1:])
        else:
            writedir = Path(outdirname)
            
        writedir.mkdir(mode=0o777, parents=True, exist_ok=True)
        with filepath.open("rb") as in_fh:
            for index, chunk in enumerate(self.data.children):
                writepath = writedir / f"{index}_{chunk.type}"
                with writepath.open("wb") as out_fh:
                    in_fh.seek(chunk.data_offset)
                    out_fh.write(in_fh.read(chunk.length))

if __name__ == "__main__":
    pass
