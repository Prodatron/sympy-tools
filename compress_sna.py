import subprocess
import sys
import glob


### ===========================================================================
### CPC EMULATOR SNAPSHOT FILE COMPRESSOR
### ===========================================================================

"""
Compresses multiple SNA files (CPC emulator snapshot file), using the ZX0
compressor by Einar Saukas, for launching with the SymSnap application on real
hardware.
Attention: Compressed SNA files can't be loaded with other emulator or tools
anymore!

usage:
python3 compress_sna.py [filemask].sna
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
    bin_crn = binary[len(binary) - 4:] + bytearray(2) + bin_crn
    return word_bin(len(bin_crn)) + bin_crn


### ---------------------------------------------------------------------------
### compress one SNA
### ---------------------------------------------------------------------------
def compress_file(file):

    print("Compressing " + file.upper() + "...")
    
    bin_out = bytearray()

    # load file
    binary = bin_load(file)
    kb = int(binary[107])
    if kb == 64:
        sizes = [4,60]
    elif kb == 128:
        sizes = [4,60,60,4]
    else:
        print("Unsupported size")
        return

    bin_out = binary[:256]
    adr = 256
    for size in sizes:
        print(f"at {adr}..")
        bin_out += compress(binary[adr:adr + size * 1024])
        adr += size * 1024

    run_cmd(f"ren {file} {file}.bak")
    bin_save(file, bin_out)

    len_org = len(binary)
    len_crn = len(bin_out)
    print(f"DONE! compressed from {len_org} to {len_crn} ({len_crn/len_org*100:.0f}%)")
    print("")


### batch
files = glob.glob(sys.argv[1])
if len(files) == 0:
    print("File(s) not found")
else:
    for file in files:
        compress_file(file)
