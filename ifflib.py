#!/usr/bin/pypy3

import struct
import os
from pathlib import Path

class chunk:
    def __init__(self):
        self.type = None
        self.length = None
        self.data = None

    def parse(self, in_fh):
        if self.type == "FORM":
            return self.parse_form(in_fh)
        else:
            return f"ERROR: Unsupported IFF base chunk '{self.type}'"

    def parse_form(self, in_fh):
        self.data = []
        
        position = 0

        buf = in_fh.read(4)
        position += 4
        self.formtype = buf.decode('ascii')

        print(self.type, self.length, self.formtype)

        # The while loop needs to be finished.
        # I am not sure whether to move this loop
        # to a separate (default) option in the
        # iff_chunk.parse method which might be
        # quite nice, and could make it much easier
        # to handle implementing CAT and LIST

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
    def __init__(self):
        self.data = None

    def load(self, filename):
        in_file = Path(filename)
        
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
