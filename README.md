# Parsing of .TGR game asset files

This repo contains attempts to reverse-engineer the .TGR files used
to store some game assets (such as images, animations, and effects)
in the TimeGate releases _Kohan: Immortal Sovereigns_ and
_Kohan: Ahriman's Gift_.
The source files under study have been extracted from the .TGW game
data archives using some tools from [the tgxlib repo](https://github.com/tim-de/tgxlib).

## Key points

* .TGR files are IFF-style files.
* They use the proprietary TGAR form type
with its own chunk types such as HEDR and FRAM.

## IFF (Interchange File Format)

IFF is a generic way of packaging data in a file that minimally
describes the format and the amount of data it contains. It is
extensible by design, and the TimeGate guys seem to have gone
down that route, creating their own _chunk_ types, rather than
using one of the [many existing formats](https://wiki.amigaos.net/wiki/IFF_FORM_and_Chunk_Registry)
for storing images and animations and things, which would have
been far more documented than what we have (you know, like some
documentation might exist (not that I'm bitter)).

The basic component of an IFF file is the _chunk_, which consists of
a 4-character type-identifier, followed by the length of the data
contained in the chunk, and then the data itself.
The length is represented as a 32-bit [**big-endian**](https://en.wikipedia.org/wiki/Endianness) integer, which
derives from IFF's origin on the Amiga, whose Motorola 68000 processor
was natively big-endian, so these values will need conversion to be
correctly read on most modern platforms.

Anyway, IFF is a pretty simple format, and there's a bunch of detailed
information about it [here](https://wiki.amigaos.net/wiki/A_Quick_Introduction_to_IFF).

The following chunks have been identified in .TGR files:

* **HEDR**: Information about the file as a whole and any following FRAM chunks

* **PALT**: Presumably a colour palette for the image (encodings not yet understood)

* **FRAM**: The actual encoded image data, utilising run-length encoding

## HEDR chunks

The header contains some information describing the file as a
whole, as well as some info about each image (FRAM chunk) stored
later in the file.

## FRAM chunks

**Note: .TGR files seem to implement a number of**
**different encodings, and the below information only**
**describes one of them, used in the larger single images**
**such as the splash screen and the menu background**

These contain a full image, comprised of lines individually
encoded and compressed. The lines each begin with a 5-byte
header formed as follows

`8X YZ 00 84 00`

where XYZ is the total length of the data forming the line
(including the 5-byte header)
and the rest seems constant.

Different encoding forms (specified within the HEDR section)
have similar information included at the start of the scanline
but encoded in different ways.
This is most likely a difference between images whose scanlines
can fit in under 256 bytes and images whose width will produce
too much data for the line length to be described with 8 bits,
and so the above line header is used.

Some form of Run Length Encoding (RLE) is utilised
to compress the lines.

It seems that the basic form of runs/pixels starts with
a single byte describing the form and length of a run
as follows:

	|7 - 5|4 - - - 0|
	|X X X|Y Y Y Y Y|

where the high order 3 bits contain flags describing the form of
data that follows it, and the low order 5 bits contain the
run length itself.

I do not fully understand the exact nature of the flag
part at this point, and am continuing to study the images
I have 

When the flag part is `001`, this seems to denote that a 2-byte encoding
describes the pixel value, so `38 00 00` denotes that there are `0x18` (24)
black pixels, and `29 00 08` indicates that there is a 9-pixel run of
`#080000`. This may, however, only be describing the channel of the image
that changes, rather than containing information about red, green, and blue.
