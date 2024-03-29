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
correctly read on x86-64 where TGR is used.

The following chunks have been identified in .TGR files:

* **HEDR**: Information about the file as a whole and any following FRAM chunks

* **PALT**: Presumably a colour palette for the image (encodings not yet understood)

* **FRAM**: The actual encoded image data, utilising run-length encoding

## HEDR chunks

The header contains some information describing the file as a
whole, as well as some info about each image (FRAM chunk) stored
later in the file.

The first 32 bits contains the version number of the program used
to generate the file. The first 16 bits contains the minor version
and the second 16 bits contains the major version.

Then there is the number of frames in the file, as a 16 bit int,
followed by the bit depth of each pixel which seems to be a u8.
The following byte is usually 0, but has been seen to be 1 sometimes,
although the meaning of this is not understood.

Following this is a 32-bit flag region, which contains information
about the encoding style of the file. Here is where the file states
whether immediate or indexed colour is being used, for example, but
it is not yet understood what information is conveyed, or how.

At offset 0x10 is the xy coordinates of the HotSpot, which for game
objects is the centre of the object on the ground. For non-game
objects this seems to always be 0.

|   | 16-bit | 16-bit |
|---|---|---|
| 0x10 | HotSpot x | HotSpot y |
| 0x14 | Selection box top left x | Selection box top left y |
| 0x18 | Selection box bottom right x | Selection box bottom right y |

The first 24 bytes of the header (after the 32-bit chunk length)
encode details about the specific format being used. I do not
understand the details of the information included in this section
yet, but I suspect that the third byte is the number of
channels contained in the images stored in the file.
One thing I have found is that the 5th byte stores the number of
FRAM chunks contained in the file.

The other bytes in this part seem to contain information about the
encoding and compression schemes used for the image data, as when
viewing files which were clearly encoded differently, some of these
numbers were different as well.

This is followed by a 32-byte section encoding the size of the image,
and seeming to give some alternative sizes (with width and/or height
either slightly smaller or bigger), although I don't yet know why
(maybe they are min and max values if the frames vary in size).

Then the file contains specifications for every FRAM chunk contained
in the file, comprised of the xy offset in the image of the top left
corner of the frame, then the offset of the bottom right corner,
stored as 16-bit integers. This is followed by the file offset of the
frame data (pointing to the beginning of the actual data in the FRAM
chunk, just after the 32-bit chunk length) represented as a 32-bit integer.

| 16-bits | 16-bits |
| --- | --- |
| upper left x | upper left y |
| lower right x | lower right y |

The header ends with some information about the rest of the chunks, including
the number of frames again, followed by what I think is some more
information about the encoding which also appeared further up in the header.

## PALT Chunks

The format of PALT colour palette specifier chunks seems to consist of a 32-bit
little-endian integer containing the number of colours stored in the palette
(which in all the examples I've looked at has just been 256), followed by an
array of all the colours in the 16-bit colour format described below.

## FRAM Chunks

**Note: .TGR files seem to implement a number of**
**different encodings, and the below information doesn't**
**describe all of them yet, and currently only covers**
**the run-length encoded bitmaps used for still images**

The FRAM chunk is the part of the container that contains the actual
image data, although the specific layout of that data depends on
several factors, such as whether the image uses immediate or indexed
colour, and the size of the image.

### Line Format
The data in each FRAM chunk consists of lines individually encoded and
compressed. Every line begins with a header which contains information
about the line that follows. The information contained is:
 1. The length of the line data in bytes (header included)
 2. The offset of the start of the line (after some transparent/background
 pixels)
 3. The number of pixels contained in the line data.

Each of these values is packed into 1 or 2 bytes, where single bytes are
used for values less than 128 and packed as-is, and values greater than
128 are packed in the form

`8X XX`

where `0X XX` is the value being encoded, and the 0x80 is used as a flag
to signify the value type being used.

### Compression Scheme

The lines are individually run-length encoded. [Run-length
encoding](https://en.wikipedia.org/wiki/Run-length_encoding) (RLE)
is a lossless compression scheme in which sections of data
consisting of the same value repeated are represented by the
number of repetitions followed by the value to be repeated.

In this case the basic form of runs/pixels starts with
a single byte describing the form and length of a run
as follows:

	|7 . 5|4 . . . 0|
	|X X X|Y Y Y Y Y|

where the high order 3 bits contain flags describing the form of
data that follows it, and the low order 5 bits contain the
run length itself.

I do not fully understand the exact nature of the flag
part at this point, and am continuing to study the images I have.

When the flag part is `001`, this seems to denote run length encoding, so
`38 00 00` denotes that there are `0x18` (24)
black pixels, and `29 00 08` indicates that there is a 9-pixel run of
`#080000`.

A flag of `010` indicates that there is a sequence of unencoded pixels, and
the run length is the number of pixels represented in this way.

The other flags that seem to be present are `110` and `111`, and each fulfil
special cases. `110` seems to occur in the bytes `0xC0` and `0xC1`, where the
first denotes a single black (`#000000`) pixel, and the latter a pixel of `#080000`.
In the case of a `111` flag, it seems again to denote the colour `#080000` but the run
length is now used to store the number of pixels of this colour. Furthermore,
for `111` bytes, there are a number of following null bytes that seems to have some
relation to the number of pixels being encoded, although this is not yet clear.

| Flag | What it Encodes | Example |
| --- | --- | --- |
| 0b000 | A run_length series of transparent pixels | 0x05 = five transparent pixels |
| 0b001 | A run_length series of identical pixels with the color defined by the next (bit_depth / 8 ) bytes | 0x25 FF FF = five white pixels
| 0b010 | A run_length series of individual pixels, each defined by (bit_depth / 8 ) bytes | 0x42 FF FF 00 00 = a white pixel followed by a black pixel
| 0b011 | A run_length series of pixels with transparency defined by the next byte and color defined by the following (bit_depth / 8 ) bytes | 0x65 07 E0 07 = five green pixels with 25% transparency |
| 0b100 | A single pixel with transparency defined by run_length and color defined by the next (bit_depth / 8 ) bytes | 0x8F E0 07 = a green pixel with 50% transparency |
| 0b101 | A run_length series of 'shadow' pixels | 0xB1 = 17 'shadow' pixels |
| 0b110 | A single player-color pixel, with color index defined by run_length | 0xC8 = a pixel with the 8th color in the player color list |
| 0b111 | A run_length series of player-color pixels, with each color index packed in 4 bits. Any remaining bits are padded with 0s to the nearest byte. This operation is used to calculate the color index: ```(4_bit_value << 1) \| 1``` | 0xE3 79 A0 = three pixels with the 15th, 18th, and 20th player colors, respectively |


### Colour format
All the images I have decoded have used 16-bit colour, with pixels arranged as follows
in the file, with bit offsets shown both within the entire 16-bit value, and within each
of the two bytes comprising it:

	F . . . B|A . . . . 5|4 . . . 0
	7 . . . 3|2 . 0|7 . 5|4 . . . 0
	R R R R R|G G G G G G|B B B B B

This arrangement is stored as if it were a big-endian 16-bit integer, so the red channel
and the top half of green are in the first byte, and the bottom 3 bits of green and the
blue channel are in the second.
