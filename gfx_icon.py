import glob
import sys

"""
===============================================================================
SYMBOS ICON GENERATOR
===============================================================================

Generates SymbOS asm/icn files from BMP graphics
image is 24x56x16 from top to down
24x24x 4    big4
 8x 8x 4    small4
24x24x16    big16
left aligned as column

supports BMP files with 4/8bpp, uncompressed, SymbOS palette


usage:
python3 gfx_icon.py [filemask]

example:

python3 gfx_icon.py *.bmp

converts all BMP in this directory to symbos icons as asm and icn files
"""



### ---------------------------------------------------------------------------
### byte to hexstr
### ---------------------------------------------------------------------------
def byt2hex(byt):
    hexstr = hex(65536 + byt)
    return hexstr[len(hexstr) - 2:]


### ---------------------------------------------------------------------------
### cut , at end of line
### ---------------------------------------------------------------------------
def cutend(txt):
    return txt[:len(txt) - 1]


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
### save text
### ---------------------------------------------------------------------------
def txt_save(file, txt):
    fil_txt = open(file, "w")
    fil_txt.write(txt)
    fil_txt.close()


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
### generates assembler code from binary
### ---------------------------------------------------------------------------
def bin2asm(asm_bin, len_head, len_line, spc, labtxt):
    asm_txt = labtxt + "\n"
    adr = len_head
    while adr < len(asm_bin):
        if (adr - len_head) % len_line == 0:
            asm_txt += f"{spc*' '}db "
        asm_txt += f"#{byt2hex(asm_bin[adr])},"
        adr += 1
        if (adr - len_head) % len_line == 0:
            asm_txt = cutend(asm_txt) + "\n"
    return asm_txt


### ---------------------------------------------------------------------------
### generates icon data from BMP
### ---------------------------------------------------------------------------
def gen_sgx_icon(file):

    fil_icn4 =  file[:len(file) - 4] + ".icn-4"
    fil_icn16 = file[:len(file) - 4] + ".icn"
    fil_asm =   file[:len(file) - 4] + ".asm"
    print(f"generating icons from {file}...")

    if file[len(file) - 4:] == '.bmp':
        bin_raw = bmp2raw(bin_load(file), 24, 56)
        if len(bin_raw) == 0:
            return
    else:
        print("unknown filetype")
        return

    bin_icn4  = sgx_block4(bin_raw,  24, 24, 00*24, 24, [0, 16, 1, 17])
    bin_icnsm = sgx_block4(bin_raw,  24,  8, 24*24,  8, [0, 16, 1, 17])
    bin_icn16 = sgx_block16(bin_raw, 24, 24, 32*24, 24)

    asm_txt  = bin2asm(bin_icnsm, 3, 16, 12, "prgicnsml   db 2,8,8")
    asm_txt += bin2asm(bin_icn4,  3, 48, 12, "prgicnbig   db 6,24,24") + "\n"
    asm_txt += bin2asm(bin_icn16, 8, 48,  0, "prgicn16c db 12,24,24:dw $+7:dw $+4,12*24:db 5")
    txt_save(fil_asm, asm_txt)

    bin_save(fil_icn4, bin_icn4)
    bin_save(fil_icn16, bytearray([12,24,24, 0,0,0,0, 32,1,5]) + bin_icn16[8:])

    print("DONE!")



### batch
if len(sys.argv) != 2:
    print("python3 gfx_icon.py [filemask]")
else:
    files = glob.glob(sys.argv[1])
    if len(files) == 0:
        print("File(s) not found")
    else:
        for file in files:
            gen_sgx_icon(file)
