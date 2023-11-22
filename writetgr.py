import tgrlib
from pathlib import Path

imagefile = tgrlib.tgrFile(Path('./GRENADIER'), 'PNG')
imagefile.load()
#imagefile.encodeLine(line_index=0)
data = b''
for frame_index in range(0,len(imagefile.img_data)):
    data += imagefile.encodeFrame(frame_index)
data = imagefile.encodeHeader(data)
data = imagefile.encodeForm(data)
with open('./outfile.tgr','wb') as fh_out:
    fh_out.write(data)



# =============================================================================
# flag = 0b010 << 5
# run_length = unique + 1
# header = flag + (run_length & 0b11111)
# out_fh.write(struct.pack('<B', header))
# if verbose:
#     print(f'  packing header {header:02X}')
# for i in range(pixel_ix,pixel_ix+run_length):
#     (r,g,b,a) = Pixel(*self.img_data[line_index*self.size[0] + pixel_ix + i]).to_int()
#     if verbose:
#         print(f'    r:{r} g:{g} b:{b} a:{a}')
#     body = (r << 11) + (g << 5) + b
#     out_fh.write(struct.pack('<H', body))
#     if verbose:
#         print(f'    packing body:{body:04X}')
# pixel_ix += run_length
# if verbose:
#     print(f'  advanced to c:{pixel_ix}')
#     
# r = 31
# g = 0
# b = 31
# body = (r << 11) + (g << 5) + b
# print(struct.pack('<H', body))
# p = Pixel.from_int(body)
# print(p)
# print(p.to_int())
# =============================================================================

