import glob
import sys


### ===========================================================================
### SYMBOS WALLPAPER CONVERTER
### ===========================================================================

"""
Converts BMP and RAW files to SymbOS wallpaper SGX files
320 x 200 x  4 (cpc, ep, nc100/200)
512 x 212 x 16 (msx, pcw, gfx9000, zx next, SymbOSVM)

supports RAW and BMP files with 4/8bpp, uncompressed;
16 colour graphics have to use the SymbOS palette


usage:
python3 gfx_wallp.py [mode] [filemask]

[mode] can be
4  -> convert 320x200x4  graphics (cpc, ep, nc100/200)
16 -> convert 512x212x16 graphics (msx, pcw, gfx9000)

example:

python3 gfx_wallp.py 4 *.bmp

converts all BMP in this directory to cpc wallpapers
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
### generates 4 colour palette translation table from BMP
### ---------------------------------------------------------------------------
def gen_pal4_sort(e):
    return e['val']

def gen_pal4(bin_bmp):
    pal = [{},{},{},{}]
    for i in range(4):
        pal[i] = {'pen': i, 'val': bin_bmp[54 + i*4 + 0] + bin_bmp[54 + i*4 + 1] + bin_bmp[54 + i*4 + 2]}
    pal.sort(key=gen_pal4_sort)

    gry = [16,17, 1, 0]     #black,darkgrey,lightgrey,white
    pen = [ 0, 0, 0, 0]
    for i in range(4):
        pen[pal[i]['pen']] = gry[i]

    return pen


### ---------------------------------------------------------------------------
### generates one SGX4 block from RAW
### ---------------------------------------------------------------------------
def sgx_block4(bin_raw, xtot, ytot, ofs, xlen, pal):
    bin_blk = bytearray([int(xlen/4), xlen, ytot])
    for i in range(ytot):
        for j in range(int(xlen / 4)):
            adr = i * xtot + ofs + j * 4
            byt = 0
            for k in range(4):
                byt += pal[bin_raw[adr + k]] * (2 ** (3-k))
            if byt > 255:
                byt = 0
            bin_blk += bytearray([byt])
    return bin_blk


### ---------------------------------------------------------------------------
### generates one SGX16 block from RAW
### ---------------------------------------------------------------------------
def sgx_block16(bin_raw, xtot, ytot, ofs, xlen):
    bin_blk = bytearray([64, 5, int(xlen/2), 0, xlen, 0, ytot, 0])
    for i in range(ytot):
        for j in range(int(xlen / 2)):
            adr = i * xtot + ofs + j * 2
            byt = bin_raw[adr] * 16 + bin_raw[adr + 1]
            if byt > 255:
                byt = 0
            bin_blk += bytearray([byt])
    return bin_blk


### ---------------------------------------------------------------------------
### generates SGX wallpaper from BMP or RAW
### ---------------------------------------------------------------------------
def gen_sgx_wallpaper(file, mode):
    if mode == "4":
        xlen = 320
        ylen = 200
    else:
        xlen = 512
        ylen = 212

    fil_sgx = file[:len(file) - 4] + ".sgx"
    print(f"converting {file} to {fil_sgx}...")

    if   file[len(file) - 4:] == '.bmp':
        bin_bmp = bin_load(file)
        bin_raw = bmp2raw(bin_bmp, xlen, ylen)
        if len(bin_raw) == 0:
            return
        pal = gen_pal4(bin_bmp)
    elif file[len(file) - 4:] == '.raw':
        bin_raw = bin_load(file)
        pal = [0, 16, 1, 17]
    else:
        print("unknown filetype")
        return

    if mode == "4":
        bin_sgx  = sgx_block4(bin_raw,  320, 200,   0, 160, pal)
        bin_sgx += sgx_block4(bin_raw,  320, 200, 160, 160, pal)
    else:
        bin_sgx  = sgx_block16(bin_raw, 512, 212,   0, 152)
        bin_sgx += sgx_block16(bin_raw, 512, 212, 152, 152)
        bin_sgx += sgx_block16(bin_raw, 512, 212, 304, 152)
        bin_sgx += sgx_block16(bin_raw, 512, 212, 456,  56)

    bin_save(fil_sgx, bin_sgx)
    print("DONE!")



### batch
if len(sys.argv) != 3:
    print("python3 gfx_wallp.py [mode] [filemask]")
    print("  mode: 4 -> 320x200x4, 16 -> 512x212x16")
elif (sys.argv[1] != "4") and (sys.argv[1] != "16"):
    print("wrong mode (must be 4 or 16)")
else:
    files = glob.glob(sys.argv[2])
    if len(files) == 0:
        print("File(s) not found")
    else:
        for file in files:
            gen_sgx_wallpaper(file, sys.argv[1])
