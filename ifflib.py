#!/usr/bin/pypy3

import struct
import os
import io
from pathlib import Path

class chunk:
    def __init__(self):
        self.type = None
        self.length = None
        self.data = None

    def parse(self, in_fh: io.BufferedReader):
        if self.type == "FORM":
            return self.parse_form(in_fh)
        else:
            return f"ERROR: Unsupported IFF base chunk '{self.type}'"

    def parse_form(self, in_fh: io.BufferedReader):
        self.data = []
        
        position = 0

        buf = in_fh.read(4)
        position += 4
        self.formtype = buf.decode('ascii')

        print(self.type, self.length, self.formtype)

        ## I am not sure whether to move this loop
        ## to a separate (default) option in the
        ## iff_chunk.parse method which might be
        ## quite nice, and could make it much easier
        ## to handle implementing CAT and LIST

        while position < self.length:
            child = chunk()
            buf = in_fh.read(4)
            child.type = buf.decode('ascii')
            buf = in_fh.read(4)
            (child.length,) = struct.unpack(">I", buf)
            child.data = in_fh.read(child.length)
            self.data.append(child)
            position += 8 + child.length + (child.length % 2)
        return position

class iff_file:
    def __init__(self, filename=None):
        self.data = None
        self.filename = filename

    def load(self):
        in_file = Path(self.filename)
        
        with in_file.open(mode="rb") as in_fh:
            self.position = 0
            self.data = chunk()
            
            buf = in_fh.read(4)
            self.position += 4
            self.data.type = buf.decode('ascii')
            
            buf = in_fh.read(4)
            self.position += 4
            (self.data.length,) =struct.unpack(">I", buf)

            self.data.parse(in_fh)

    def dump(self, outdirname=None):
        if outdirname == None:
            filepath = Path(self.filename)
            writedir = Path(filepath.stem + '_' + filepath.suffix[1:])
        else:
            writedir = Path(outdirname)
            
        writedir.mkdir(mode=0o777, parents=True, exist_ok=True)
            
        for index, chunk in enumerate(self.data.data):
            writepath = writedir / f"{index}_{chunk.type}"
            with writepath.open("wb") as out_fh:
                out_fh.write(chunk.data)
