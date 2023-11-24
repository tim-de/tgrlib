#!/usr/bin/pypy3

import sys
import tgrlib
import argparse
from PIL import Image
from pathlib import Path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                        prog='readfram.py',
                        description='Reads a .TGR asset file and extracts each image frame to a .PNG',
                        epilog='')
    
    parser.add_argument('image_path')
    parser.add_argument('-c', '--color', choices=range(1,9), default=2, type=int, help='Use the specified player color for extracted sprites. Defaults to 2 (blue)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable debugging printouts')
    parser.add_argument('--no-align-frames', action='store_true', help='Disable frame alignment within image size')
    parser.add_argument('--single-frame', default=-1, type=int, help='Extract only the specified frame')
    
    args = parser.parse_args()
    
    image_path = args.image_path
    
    player_color = args.color

    imagefile = tgrlib.tgrFile(image_path, 'TGR', False)

    imagefile.load()

    image_name = Path(image_path).stem

    Path(image_name).mkdir(exist_ok=True)

    frame_index = 0
    pixel_format = "RGBA"

    for frame_index, frame in enumerate(imagefile.frames):
        if args.single_frame != -1 and args.single_frame != frame_index:
            continue
    #print(imagefile.framecount)
    # frame = imagefile.frames[frame_index]

        print(frame_index, frame.size)
        if args.no_align_frames:
            image = Image.new(pixel_format, frame.size)
        else:
            image = Image.new(pixel_format, imagefile.size)
            fram_img = Image.new(pixel_format, frame.size)
        imagedata = b""
        with open(image_path, "rb") as in_fh:
            for idx in range(len(frame.lines)):
                rawline = imagefile.extractLine(in_fh, frame_index=frame_index, line_index=idx, increment=0, color=player_color)
                #print(f"{idx+1:3d}: 0x{frame.lines[idx].offset:06x}, {len(rawline)}")
                if len(rawline) < frame.size[0]:
                    rawline += [tgrlib.transparency for _ in range(frame.size[0] - len(rawline))]
                #while len(rawline) < frame.size[0]:
                #    rawline.append(tgrlib.Pixel(0, 0, 0))
                if len(rawline) > frame.size[0]:
                    rawline = rawline[0:frame.size[0]]
                imagedata += b"".join([elem.pack_to_bin(pixel_format) for elem in rawline])
                #print(len(imagedata))
        target_len = (frame.size[0] * frame.size[1]) * (3 if format == "RGB" else 4)
        if len(imagedata) < target_len:
            imagedata += bytes([0x00 for _ in range(target_len - len(imagedata))])
        if args.no_align_frames:
            image.frombytes(imagedata)
        else:
            fram_img.frombytes(imagedata)
            offset = imagefile.frameoffsets[frame_index][0]
            image.paste(fram_img, offset)
        image.save(f"{image_name}/fram_{frame_index:04d}.png")

        #image.save(f"{image_name}.png")
