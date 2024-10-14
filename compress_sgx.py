import subprocess
import sys
import math
import glob


### ===========================================================================
### SGX GRAPHIC COMPRESSOR
### ===========================================================================

"""
Compresses multiple SGX graphic file, using the ZX0 compressor by Einar Saukas.

usage:
python3 compress_sgx.py [filemask].sgx
"""


### ---------------------------------------------------------------------------
### execute shell command
### ---------------------------------------------------------------------------
def run_cmd(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    c = p.communicate()


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
### return word as binary
### ---------------------------------------------------------------------------
def word_bin(word):
    return bytearray([word % 256, int(word/256)])


### ---------------------------------------------------------------------------
### compress data
### ---------------------------------------------------------------------------
def compress(binary):
    bin_save("temp", binary[:len(binary) - 4])
    run_cmd("-zx0 temp")
    bin_crn = bin_load("temp.zx0")
    run_cmd("del temp")
    run_cmd("del temp.zx0")
    return binary[len(binary) - 4:] + bytearray(2) + bin_crn


### ---------------------------------------------------------------------------
### compress simple graphic part
### ---------------------------------------------------------------------------
def compress_smp(binary, i):

    print(f"part {i} simple..")
    bin_len = binary[0] * binary[2]
    if len(binary) + 3 < bin_len:
        return bytearray(), bytearray(1)
    bin_crn = compress(binary[3:3 + bin_len])

    return bytearray([128 + binary[0]]) + binary[1:3] + word_bin(len(bin_crn)) + bin_crn, binary[3 + bin_len:]


### ---------------------------------------------------------------------------
### compress extended graphic part
### ---------------------------------------------------------------------------
def compress_ext(binary, i):

    print(f"part {i} extended..")
    bin_len = (binary[2] + binary[3] * 256) * (binary[6] + binary[7] * 256)
    if len(binary) + 8 < bin_len:
        return bytearray(), bytearray(1)

    if binary[1] == 0:
        max_len = 63        # xlen in bytes maximum for 4...
    else:
        max_len = 126       # and 16 colours
    max_len = 16384 - 256 - 10 * int(math.ceil(binary[2] / max_len))
                            # maxlen per block = 16384-256-10*number of heads

    bin_data = binary[8:8 + bin_len]
    bin_out = bytearray([128 + 64]) + binary[1:8]
    while len(bin_data) > 0:
        bin_crn = compress(bin_data[:max_len])
        bin_out += word_bin(len(bin_crn)) + bin_crn
        bin_data = bin_data[max_len:]

    return bin_out, binary[8 + bin_len:]


### ---------------------------------------------------------------------------
### compress one SGX file
### ---------------------------------------------------------------------------
def compress_sgx(file):

    print("Compressing " + file.upper() + "...")
    
    bin_out = bytearray()

    # load exe
    bin_sgx = bin_load(file) + bytearray(1)
    if int(bin_sgx[0]) > 128:
        print("File already compressed")
        print("")
        return
    len_org = len(bin_sgx)

    # chunks
    i = 1
    while bin_sgx[:1] != bytearray(1):
        if (bin_sgx[0] > 0) and (bin_sgx[0] < 64):
            bin_crn, bin_sgx = compress_smp(bin_sgx, i)
            i += 1
        elif bin_sgx[0] == 64:
            bin_crn, bin_sgx = compress_ext(bin_sgx, i)
            i += 1
        elif bin_sgx[0] == 255:
            bin_crn = bytearray([255,0,0])
            bin_sgx = bin_sgx[3:]
            print("linefeed..")
        else:
            break
        bin_out += bin_crn
    bin_out += bytearray(3)

    # save compressed sgx
    run_cmd(f"ren {file} {file}.bak")
    bin_save(file, bin_out)

    len_crn = len(bin_out)
    print(f"DONE! compressed from {len_org} to {len_crn} ({len_crn/len_org*100:.0f}%)")
    print("")


### batch
files = glob.glob(sys.argv[1])
if len(files) == 0:
    print("File(s) not found")
else:
    for file in files:
        compress_sgx(file)
