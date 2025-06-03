# -*- coding: utf-8 -*-
"""
Created on Mon Jun  2 16:47:13 2025

@author: sceadu37
"""

from pathlib import Path
from argparse import Namespace
from random import randint
import tgrtool

asset_path = Path.home() / "Documents/KAG/ExtractedGameFiles/Kohan_ag/ART/"
print(f"unpacking all .TGR files in {asset_path}")

#iterate through all (sub) directories and unpack each file
walk = (x for x in asset_path.walk())



while True:
    try:
        folder = next(walk)
        #print(folder[0])
        for file in folder[2]:
            file_path = folder[0] / file
            out_path = Path("./test") / file_path.relative_to(asset_path)
            #print(out_path)
            args = Namespace(color=randint(0, 11),
                             no_align_frames=False,
                             fx_error_fix=True,
                             single_frame=-1,
                             output=out_path,
                             config=None,
                             verbose=False,
                             source=file_path)
            try:
                tgrtool.unpack(args)
            except Exception:
                print(f"Failed to extract {file_path}")
    except StopIteration:
        break
