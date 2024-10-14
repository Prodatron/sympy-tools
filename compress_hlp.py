import subprocess
import sys
import glob


### ===========================================================================
### HELP FILE COMPRESSOR
### ===========================================================================

"""
Compresses multiple HLP files (SymbOS help file browser), using the ZX0
compressor by Einar Saukas.

usage:
python3 compress_exe.py [filemask].hlp
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
### get word from binary
### ---------------------------------------------------------------------------
def word_get(binary):
    return binary[0] + 256 * binary[1]


### ---------------------------------------------------------------------------
### return word as binary
### ---------------------------------------------------------------------------
def word_bin(word):
    return bytearray([word % 256, int(word/256)])


### ---------------------------------------------------------------------------
### compress help chapter
### ---------------------------------------------------------------------------
def compress(binary):
    if len(binary) > 2 + 2 + 4 + 1:
        bin_save("temp", binary[:len(binary) - 4])
        run_cmd("-zx0 temp")
        bin_crn = bin_load("temp.zx0")
        run_cmd("del temp")
        run_cmd("del temp.zx0")
        bin_crn = binary[len(binary) - 4:] + bytearray(2) + bin_crn
        if (len(bin_crn) + 2) < len(binary):
            return word_bin(len(bin_crn)) + bin_crn, 128
    return binary, 0


### ---------------------------------------------------------------------------
### compress one HLP file
### ---------------------------------------------------------------------------
def compress_hlp(file):

    print("Compressing " + file.upper() + "...")
    
    bin_out = bytearray()

    # load hlp
    binary = bytearray(bin_load(file))
    hlpid = bytearray()
    hlpid.extend("SYMHLP10".encode())
    if binary[:8] != hlpid:
        print("Not a SymbOS help file")
        print("")
        return

    len_org = len(binary)
    bin_out = bytearray()

    len_head = 8 + 2 + 2 + word_get(binary[8:10]) + word_get(binary[10:12])

    adr = len_head
    for i in range(int(word_get(binary[8:10])/4)):
        len_chap = word_get(binary[12 + i * 4:14 + i *4]) & 8191
        bin_chap = binary[adr:adr + len_chap]
        hed_chap = bin_chap[:2 + bin_chap[1] * 4]
        if int(hed_chap[0]) >= 128:
            print("File already compressed")
            print("")
            return
        org_chap = bin_chap[len(hed_chap):]
        crn_chap, crn_flag = compress(org_chap)
        col_flag = word_get(binary[12 + i * 4:14 + i *4]) & 8192

        binary[12 + i * 4:14 + i *4] = word_bin(col_flag + len(hed_chap) + len(crn_chap))
        hed_chap[0] = int(hed_chap[0]) + crn_flag
        bin_out += hed_chap + crn_chap

        adr += len_chap

    bin_out = binary[:len_head] + bin_out

    # save compressed hlp
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
        compress_hlp(file)
