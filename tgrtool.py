#!/usr/bin/python

import argparse
import tgrlib
import struct
from pathlib import Path
from PIL import Image

def unpack(args: argparse.Namespace):
    image_path = args.source
    print(image_path)
    print(Path(image_path))
    player_color = args.color
    imagefile = tgrlib.tgrFile(image_path, False)
    imagefile.load()

    if args.output != None:
        image_name = args.output
    else:
        image_name = Path(image_path).stem
    print(args.output)
    print(image_name)
    Path(image_name).mkdir(exist_ok=True, parents=True)

    frame_index = 0
    pixel_format = "RGBA"
    for frame_index, frame in enumerate(imagefile.frames):
        
        # Check for padding (blank) frames
        if frame.size == (0, 0,):
            print(f'padding frame {frame_index}')
            imagefile.padding_frames.append(frame_index)
            image = Image.new('RGBA',(1,1),(0,0,0,0))
            image.save(f"{image_name}/fram_{frame_index:04d}.png")
            continue            
        
        if args.single_frame != -1 and args.single_frame != frame_index:
            continue
    #print(imagefile.framecount)
    # frame = imagefile.frames[frame_index]

        print(frame_index, frame.size)
        imagedata = b""
        with open(image_path, "rb") as in_fh:
            for idx in range(len(frame.lines)):
                rawline = imagefile.extractLine(in_fh, frame_index=frame_index, line_index=idx, increment=0, color=player_color, fx_error_fix=args.fx_error_fix)
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
            image = Image.new(pixel_format, frame.size)
            image.frombytes(imagedata)
        else:
            image = Image.new(pixel_format, imagefile.size)
            fram_img = Image.new(pixel_format, frame.size)
            fram_img.frombytes(imagedata)
            offset = imagefile.frameoffsets[frame_index][0]
            image.paste(fram_img, offset)
        image.save(f"{image_name}/fram_{frame_index:04d}.png")
    if args.config:
        config_path = args.config
    else:
        config_path = f"{image_name}/sprite.ini"
    imagefile.write_config(config_path)

def pack(args: argparse.Namespace):
    imagefile = tgrlib.tgrFile(args.source)
    print(imagefile.imgs[0].mode)
    config_path = args.config if args.config else f"{args.source}/sprite.ini"
    
    if args.portrait != None:
        imagefile.resize(args.portrait)
        imagefile.addPortraitFrame(args.portrait)
    
    imagefile.load(config_path, args.no_crop)
    
    if args.output != '' and args.output != None:
        dest_path = Path(args.output)
        if dest_path.suffix.upper() == '.TGR':
            filename = dest_path.name
            dest_path = dest_path.parent
        else:
            filename = imagefile.filename.stem + '.tgr'
            
        dest_path.mkdir(exist_ok=True, parents=True)
        outfile = dest_path / filename
    else:
        outfile = imagefile.filename.stem + '.tgr'
    
    data = b''
    for frame_index in range(0,len(imagefile.img_data)):
        if frame_index in imagefile.padding_frames:
            imagefile.frameoffsets.append(0)
            data += struct.pack('4sI', b'FRAM', 0)
        else:
            imagefile.frameoffsets.append(len(data))
            data += imagefile.encodeFrame(frame_index, color=args.color)
    data = imagefile.encodeHeader(data)
    data = imagefile.encodeForm(data)
    print("writing to: ", outfile)
    with open(outfile ,'wb') as fh_out:
        fh_out.write(data)

# from https://stackoverflow.com/a/34256516
# Allows filepaths with spaces to be parsed correctly
class MyAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, ' '.join(values))


## Define parsers
main_parse = argparse.ArgumentParser(prog="tgrtool")

sub_parsers = main_parse.add_subparsers(required=True, help="available commands")

unpack_parse = sub_parsers.add_parser("unpack")
unpack_parse.set_defaults(func=unpack)
unpack_parse.add_argument('-c', '--color', choices=range(1,12), default=2, type=int, help='use the specified player color for extracted sprites. Defaults to 2 (blue)')
unpack_parse.add_argument('-v', '--verbose', action='store_true', help='enable debugging printouts')
unpack_parse.add_argument('--no-align-frames', action='store_true', help='disable frame alignment within image size')
unpack_parse.add_argument('--single-frame', default=-1, type=int, help='extract only the specified frame')
unpack_parse.add_argument('--fx-error-fix', action='store_true', help='use this if non-unit .TGR files have multicolored horizontal stripes in the output')
unpack_parse.add_argument('-o', '--output', type=str, default=None, help='destination directory for unpacked files')
unpack_parse.add_argument('--config', type=str, help="path to write sprite config file")
unpack_parse.add_argument('source', type=str, help='path to target tgr file', nargs='+', action=MyAction)

pack_parse = sub_parsers.add_parser("pack")
pack_parse.set_defaults(func=pack)
pack_parse.add_argument('-c', '--color', choices=range(1,12), default=None, type=int, help='Specify the color list used for player-colored pixels. Pixels matching the list will be converted to player pixels')
pack_parse.add_argument('-o', '--output', type=str, help='destination file for packed data')
pack_parse.add_argument('--config', type=str, help='path to sprite config file')
pack_parse.add_argument('--no-crop', action='store_true', help='Disable automatic cropping of transparent background pixels')
pack_parse.add_argument('--portrait', choices=('large','small'), default=None, type=str, help='Specify the size of the portrait. Choose small for company/sidebar portraits, or large for campaign dialogue portraits')
pack_parse.add_argument('source', type=str, help='path to file or directory to unpack', nargs='+', action=MyAction)

if __name__ == '__main__':
    if tgrlib.is_exe:
        print('Welcome to TGR Tool. Please enter a command, or type "--help" for help, or "exit" to exit')
        
        while True:
            command = input('tgrtool > ')
        
            if command.lower() == 'exit':
                print('Exiting')
                break
            try:              
                args = main_parse.parse_args(command.split(' '))
                args.func(args)
            except SystemExit:
                print('')
    else:
        args = main_parse.parse_args()
        args.func(args)
