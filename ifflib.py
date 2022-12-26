#!/usr/bin/pypy3

import struct
import os
from pathlib import Path

class iff_chunk:
    def __init__(self):
        self.type = None
        self.length = None
        self.children = None

    def parse(self, filehandle):
        if type == "FORM":
            return self.parse_form(in_fh)
        else:
            return "ERROR: Unsupported IFF base chunk '{type}'"

    def parse_form(self, in_fh):
        position = 0
        
        buf = in_fh.read(4)
        position += 4
        (self.length,) = struct.unpack(">I", buf)

        buf = in_fh.read(4)
        position += 4
        (self.formtype,) = buf.decode('ascii')

        # The while loop needs to be finished.
        # I am not sure whether to move this loop
        # to a separate (default) option in the
        # iff_chunk.parse method which might be
        # quite nice, and could make it much easier
        # to handle implementing CAT and LIST

        while position < self.length:
            buf = in_fh.read(4)
            chunk = iff_chunk()
            chunk.type = buf.decode('ascii')
            buf = in_fh.read(4)
            (chunk.length,) = struct.unpack(">I", buf)

class iff_file:
    def __init__(self):
        self.chunks = None

    def load(self, filename):
        in_file = Path(filename)
        
        with in_file.open(mode="rb") as in_fh:
            self.position = 0
            self.data = iff_chunk()
            
            buf = in_fh.read(4)
            self.position += 4
            self.data.type = buf.decode('ascii')
            
            buf = in_fh.read(4)
            self.position += 4
            (self.data.length,) =struct.unpack(">I", buf)

            self.data.parse(in_fh)
