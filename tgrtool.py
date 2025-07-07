#!/usr/bin/python

import argparse
import tgrlib
import struct
from pathlib import Path
from PIL import Image
import sys
from PyQt5 import QtWidgets

import interface

def unpack(args: argparse.Namespace):
    tgrlib.verbose = args.verbose
    image_path = args.source
    print(f"[Info] extracting data from {Path(image_path).resolve()}") if tgrlib.verbose > 0 else None
    tgr = tgrlib.tgrFile(image_path)
    tgr.load()

    if args.output != None:
        image_name = args.output
    else:
        image_name = Path(image_path).stem
    print(f"[Info] writing data to {Path(image_name).resolve()}") if tgrlib.verbose > 0 else None
    Path(image_name).mkdir(exist_ok=True, parents=True)

    if args.sprite_sheet:
        width = 0    # width of the sprite sheet in frames
        height = 0   # height of the sprite sheet in frames
        for anim in tgr.animations:
            if anim[1] > width:   # if animation's frame count is greater than the width:
                width = anim[1]   # set the width to this animation's frame count
            height += anim[2]     # increase height by 1 for each view angle in this animation
        width *= tgr.size[0]  # scale width and height by the dimensions of an idividual frame
        height *= tgr.size[1]
        sprite_sheet = Image.new('RGBA', (width, height), (0,0,0,0))

    for frame_index, (frame, box) in enumerate(zip(tgr.frames, tgrlib.spriteSheetBoxIter(tgr.size, tgr.animations))):
        
        if args.single_frame != -1 and args.single_frame != frame_index:
            continue
        
        print(f"[Info] unpacking frame {frame_index} with size {frame.size}") if tgrlib.verbose > 0 else None
        image = unpack_frame(tgr,
                             frame_index,
                             color=args.color,
                             fx_error_fix=args.fx_error_fix,
                             align_frames=(not args.no_align_frames))
        
        if args.sprite_sheet:
            sprite_sheet.paste(image, box)
        else:
            image.save(f"{image_name}/fram_{frame_index:04d}.png")
    
    if args.sprite_sheet:
        sprite_sheet.save(f"{image_name}/sprite_sheet.png")
    
    if args.config:
        config_path = args.config
    else:
        config_path = f"{image_name}/sprite.ini"
    tgr.write_config(config_path)

# unpacks a single frame and returns it as a pillow image object
def unpack_frame(tgr, frame_index, color=1, fx_error_fix=False, align_frames=True, pixel_format="RGBA"):
    imagedata = b""
    with open(tgr.filename, "rb") as in_fh:
        frame = tgr.frames[frame_index]
        
        # Check for padding (blank) frames
        if frame.size == (0, 0,):
            tgr.padding_frames.append(frame_index)
            image = Image.new('RGBA',(1,1),(0,0,0,0))
            return image
        
        for idx in range(len(frame.lines)):
            #print(f'reading frame {frame_index} line {idx}')
            rawline = tgr.extractLine(in_fh, frame_index=frame_index, line_index=idx, increment=0, color=color, fx_error_fix=fx_error_fix)
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
    if not align_frames:
        image = Image.new(pixel_format, frame.size)
        image.frombytes(imagedata)
    else:
        image = Image.new(pixel_format, tgr.size)
        fram_img = Image.new(pixel_format, frame.size)
        fram_img.frombytes(imagedata)
        offset = tgr.frameoffsets[frame_index][0]
        image.paste(fram_img, offset)
    
    return image


def pack(args: argparse.Namespace):
    tgrlib.verbose = args.verbose
    tgr = tgrlib.tgrFile(args.source)
    
    if args.portrait != None:
        tgr.resize(args.portrait)
        tgr.addPortraitFrame(args.portrait)
    
    tgr.load(args.config, args.no_crop)
    
    if args.output != '' and args.output != None:
        dest_path = Path(args.output)
        if dest_path.suffix.upper() == '.TGR':
            filename = dest_path.name
            dest_path = dest_path.parent
        else:
            filename = tgr.filename.stem + '.tgr'
            
        dest_path.mkdir(exist_ok=True, parents=True)
        outfile = dest_path / filename
    else:
        outfile = tgr.filename.stem + '.tgr'
    
    data = b''
    for frame_index in range(0,len(tgr.img_data)):
        if frame_index in tgr.padding_frames:
            tgr.frameoffsets.append(0)
            data += struct.pack('4sI', b'FRAM', 0)
        else:
            tgr.frameoffsets.append(len(data))
            data += tgr.encodeFrame(frame_index, color=args.color)
    data = tgr.encodeHeader(data)
    data = tgr.encodeForm(data)
    print("writing to: ", outfile) if tgrlib.verbose > 0 else None
    with open(outfile ,'wb') as fh_out:
        fh_out.write(data)

# from https://stackoverflow.com/a/34256516
# Allows filepaths with spaces to be parsed correctly
class MyAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, ' '.join(values))


## Define parsers
main_parse = argparse.ArgumentParser(prog="tgrtool")
main_parse.add_argument('--no-gui', action='store_true', help='run tgrtool through its command-line interface')

sub_parsers = main_parse.add_subparsers(help="available commands")

unpack_parse = sub_parsers.add_parser("unpack")
unpack_parse.set_defaults(func=unpack)
unpack_parse.add_argument('-c', '--color', choices=range(1,12), default=2, type=int, help='use the specified player color for extracted sprites. Defaults to 2 (blue)')
unpack_parse.add_argument('-v', '--verbose', action='count', default=0, help='enable levels of debugging printouts (add more v for higher verbosity)')
unpack_parse.add_argument('--sprite-sheet', action='store_true', help='save images to a sprite sheet instead of individual files')
unpack_parse.add_argument('--no-align-frames', action='store_true', help='disable frame alignment within image size')
unpack_parse.add_argument('--single-frame', default=-1, type=int, help='extract only the specified frame')
unpack_parse.add_argument('--fx-error-fix', action='store_true', help='use this if non-unit .TGR files have multicolored horizontal stripes in the output')
unpack_parse.add_argument('-o', '--output', type=str, default=None, help='destination directory for unpacked files')
unpack_parse.add_argument('--config', type=str, help="path to write sprite config file")
unpack_parse.add_argument('source', type=str, help='path to target tgr file', nargs='+', action=MyAction)

pack_parse = sub_parsers.add_parser("pack")
pack_parse.set_defaults(func=pack)
pack_parse.add_argument('-c', '--color', choices=range(1,12), default=None, type=int, help='Specify the color list used for player-colored pixels. Pixels matching the list will be converted to player pixels')
pack_parse.add_argument('-v', '--verbose', action='count', default=0, help='enable levels of debugging printouts (add more v for higher verbosity)')
pack_parse.add_argument('-o', '--output', type=str, help='destination file for packed data')
pack_parse.add_argument('--config', default=None, type=str, help='path to sprite config file')
pack_parse.add_argument('--no-crop', action='store_true', help='Disable automatic cropping of transparent background pixels')
pack_parse.add_argument('--portrait', choices=('large','small'), default=None, type=str, help='Specify the size of the portrait. Choose small for company/sidebar portraits, or large for campaign dialogue portraits')
pack_parse.add_argument('source', type=str, help='path to file or directory to unpack', nargs='+', action=MyAction)

if __name__ == '__main__':
        args = main_parse.parse_args()
        if args.no_gui:
            if hasattr(args, 'func'):
                args.func(args)
            else:
                print("usage: tgrtool [-h] [--no-gui] {unpack,pack} ...\ntgrtool: error: the following arguments are required: {unpack,pack}")
                exit()
        else:
            app = QtWidgets.QApplication(sys.argv)
            main_window = interface.MainWindow()
            main_window.show()
            app.exec()