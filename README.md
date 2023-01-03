# Parsing of .TGR game asset files

## Key points

* .TGR files are IFF-style files.
* They use the proprietary TGAR form type
with its own chunk types such as HEDR and FRAM.

## FRAM chunks

**Note: .TGR files seem to implement a number of**
**different encodings, and the below information only**
**describes one of them, used in the larger single images**
**such as the splash screen and the menu background**

?These contain a full image, comprised of lines individually
encoded and compressed. The lines each begin with a 5-byte
header formed as follows

`8X YZ 00 84 00`

where XYZ is the total length of the data forming the line
(including the 5-byte header)
and the rest seems constant.

Some form of Run Length Encoding (RLE) is utilised
to compress the lines.

It seems that the basic form of runs/pixels starts with
a single byte describing the form and length of a run
as follows:

|`8 - 6`|`5 - - - - 0`|</br>
|`X X X`|`Y Y Y Y Y Y`|

where the high order 3 bits contain flags describing the form of
data that follows it, and the low order 5 bits contain the
run length itself.

I do not fully understand the exact nature of the flag
part at this point, and am continuing to study the images
I have 
