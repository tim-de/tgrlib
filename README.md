Parsing of .TGR game asset files
===============================

Key points
----------

* .TGR files are IFF-style files.
* They use the proprietary TGAR form type
with its own chunk types such as HEDR and FRAM.

FRAM chunks
-----------

These contain a full image, comprised of lines individually
encoded and compressed. The lines each begin with a 5-byte
header formed as follows

`8X YZ 00 84 00'

where XYZ is the length of the data forming the line,
and the rest seems constant.

Currently I am assuming that it uses some form of Run Length
Encoding (RLE) to compress the lines