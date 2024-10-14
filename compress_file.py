import subprocess
import sys
import glob


### ===========================================================================
### GENERAL FILE COMPRESSOR
### ===========================================================================

"""
Compresses multiple files of different types handled by SymbOS applications
(currently SymAmp only), using the ZX0 compressor by Einar Saukas.

This can be done for the following music files:
- ST2 (compiled Soundtrakker 128)
- SKM (compiled Starkos Tracker)
- PT3 (Protracker 3, Vortex Tracker)
- SA2 (Surprise! Adlib Tracker 2)
Attention: Compressed files can't be loaded with other tools anymore!

usage:
python3 compress_file.py [filemask]
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
### compress one general file
### ---------------------------------------------------------------------------
def compress_file(file):

    print("Compressing " + file.upper() + "...")
    
    # load file
    binary = bin_load(file)

    bin_out = bytearray()
    bin_out.extend("SymZX0".encode())
    if binary[:6] == bin_out:
        print("File already compressed")
        print("")
        return

    len_org = len(binary)
    bin_out += word_bin(len_org) + compress(binary)

    # save compressed file
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
        compress_file(file)
