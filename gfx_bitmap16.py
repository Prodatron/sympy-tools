import subprocess
import sys
import glob


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
### generates sgx16 from RAW
### ---------------------------------------------------------------------------
def gen_asm16(bin_raw, xlen, ylen):
    txt_asm = f"gfx16c db {int(xlen/2)},{xlen},{ylen}:dw $+7,$+4,{xlen}*{ylen}:db 5\n"
    for i in range(ylen):
        txt_asm += "db "
        for j in range(0, xlen, 2):
            byt = bin_raw[i * xlen + j] * 16 + bin_raw[i * xlen + j + 1]
            hexstr = hex(65536 + byt)
            hexstr = hexstr[len(hexstr) - 2:]
            txt_asm += f"#{hexstr},"
        txt_asm = txt_asm[:len(txt_asm)-1] + "\n"
    print(txt_asm)


### ---------------------------------------------------------------------------
### generates sgx4 from BMP
### ---------------------------------------------------------------------------
def gen_sgx16(file, xlen, ylen):

    fil_sgx16 = file[:len(file) - 4] + ".sgx"

    if file[len(file) - 4:] == '.bmp':
        bin_raw = bmp2raw(bin_load(file), xlen, ylen)
        if len(bin_raw) == 0:
            return
    else:
        print("unknown filetype")
        return

    #bin_sgx4  = sgx_block4(bin_raw, xlen, ylen, 0, xlen, [0, 16, 1, 17])
    gen_asm16(bin_raw, xlen, ylen)
    #bin_save(fil_sgx4, bin_sgx4)

    print("DONE!")


### batch
if len(sys.argv) != 4:
    print("python3 gfx_bitmap4.py [filemask] [xlen] [ylen]")
else:
    files = glob.glob(sys.argv[1])
    if len(files) == 0:
        print("File(s) not found")
    else:
        for file in files:
            gen_sgx16(file, int(sys.argv[2]), int(sys.argv[3]))
