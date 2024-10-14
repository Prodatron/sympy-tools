import glob
import sys


"""
===============================================================================
RAW FONT CONVERTER
===============================================================================

Converts BMP files to raw font files
supports BMP files with 4/8bpp, uncompressed;
graphic must be 2 colour indexed, colour 0 paper, colour 1 pen

usage:
python3 gfx_font.py [x] [y] [h] [filemask]

[x] -> chars per line (always 8 pixel width)
[y] -> chars per column
[h] -> char height in pixels (1-15)

example:

python3 gfx_font.py 16 16 8 *.bmp
"""


### ---------------------------------------------------------------------------
### get word from binary
### ---------------------------------------------------------------------------
def word_get(binary):
    return binary[0] + 256 * binary[1]


### ---------------------------------------------------------------------------
### load binary
### ---------------------------------------------------------------------------
def bin_load(file):
    fil_bin = open(file, "rb")
    binary = fil_bin.read()
    fil_bin.close()
    return binary


### ---------------------------------------------------------------------------
### save binary
### ---------------------------------------------------------------------------
def bin_save(file, binary):
    fil_bin = open(file, "wb")
    fil_bin.write(binary)
    fil_bin.close()


### ---------------------------------------------------------------------------
### generates RAW from BMP
### ---------------------------------------------------------------------------
def bmp2raw(bin_bmp, xlen, ylen):
    bin_raw = bytearray()

    # check for valid BMP parameters
    xorg = word_get(bin_bmp[18:20])
    yorg = word_get(bin_bmp[22:24])
    if bin_bmp[25] > 128:
        yorg = 65536 - yorg
    if (xorg != xlen) or (yorg != ylen):
        print(f"wrong image size; must be {xlen} x {ylen}")
    elif (bin_bmp[28] != 8) and (bin_bmp[28] != 4):
        print("unsupported colourdepth; must be 4 or 8 bpp")
    elif bin_bmp[30] != 0:
        print("file must be uncompressed")
    else:

        if bin_bmp[28] == 4:
            xbyt = int(xlen/2)
        else:
            xbyt = xlen

        adr_beg = word_get(bin_bmp[10:12])
        for i in range(ylen):
            if bin_bmp[25] > 128:
                adr_lin = adr_beg + i * xbyt
            else:
                adr_lin = adr_beg + (ylen - 1 - i) * xbyt

            if bin_bmp[28] == 4:
                for i in range(xbyt):
                    bin_raw += bytearray([int(bin_bmp[adr_lin + i] / 16), bin_bmp[adr_lin + i] % 16])
            else:
                bin_raw += bin_bmp[adr_lin:adr_lin + xlen]

    return bin_raw


### ---------------------------------------------------------------------------
### generates FNT from RAW
### ---------------------------------------------------------------------------
def raw2fnt(bin_raw, xcount, ycount, yheight, cstart):
    bin_fnt = bytearray(cstart * yheight)
    for y in range(ycount):
        for x in range(xcount):
            for l in range(yheight):
                byt = 0
                for b in range(8):
                    adr = y*yheight*8*xcount + l*xcount*8 + x*8 + b
                    byt = byt * 2 + bin_raw[adr]
                bin_fnt += bytearray([byt])
    
    return bin_fnt

### ---------------------------------------------------------------------------
### generates FNT from BMP or RAW
### ---------------------------------------------------------------------------
def gen_fnt(file, xcount, ycount, yheight, cstart):
    print(file, xcount, ycount, yheight, cstart)

    xlen = xcount * 8
    ylen = ycount * yheight

    fil_fnt = file[:len(file) - 4] + ".fnt"
    print(f"converting {file} to {fil_fnt}...")

    if file[len(file) - 4:] == '.bmp':
        bin_bmp = bin_load(file)
        bin_raw = bmp2raw(bin_bmp, xlen, ylen)
        if len(bin_raw) == 0:
            return
        bin_fnt = raw2fnt(bin_raw, xcount, ycount, yheight, cstart)
    else:
        print("unknown filetype")
        return

    bin_save(fil_fnt, bin_fnt)
    print("DONE!")


### batch
if len(sys.argv) != 6:
    print("python3 gfx_font.py [xcount] [ycount] [yheight] [first char] [filemask]")
else:
    files = glob.glob(sys.argv[5])
    if len(files) == 0:
        print("File(s) not found")
    else:
        for file in files:
            gen_fnt(file, int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
