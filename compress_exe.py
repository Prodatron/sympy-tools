import subprocess
import sys
import glob


### ===========================================================================
### EXECUTABLE COMPRESSOR
### ===========================================================================

"""
Compresses multiple SymbOS executables, using the ZX0 compressor by Einar
Saukas. Files can be EXE (executable), SAV (screen saver), WDG (desktop
widget), COM (SymShell executable).

usage:
python3 compress_exe.py [filemask]
"""


HD_FUL_CODE =  0  # Length of the code area
HD_FUL_DATA =  2  # Length of the data area
HD_FUL_TRNS =  4  # Length of the transfer area
HD_FUL_RELC =  8  # Size of the relocator table (=total size/2)
HD_FLAGS    = 40  # Flags (+1=16 colour icon included, +2=packed reloc table, +128=compressed code, +64=compressed data, +32=compressed transfer, +16=compressed reloc)
HD_ICONOFS  = 41  # 16 colour icon offset in file


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
### set word in header
### ---------------------------------------------------------------------------
def word_set(compressed, binary, adr, word):
    if compressed:
        binary[adr+0] = word % 256
        binary[adr+1] = int(word/256)


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
### compress one area
### ---------------------------------------------------------------------------
def compress_area(name, uncompressed, binary):

    print(name + "..")

    if len(binary) > 8 and uncompressed > -1:
    
        # create and compress file
        bin_save("temp", binary[:len(binary)-4])

        if uncompressed == 0:
            run_cmd("-zx0 temp")
        else:
            run_cmd(f"-zx0 +{uncompressed} temp")
    
        # load compressed data and remove temps
        bin_crn = bin_load("temp.zx0")
        run_cmd("del temp")
        run_cmd("del temp.zx0")
    
        bin_crn = binary[len(binary)-4:] + word_bin(uncompressed) + binary[:uncompressed] + bin_crn
        bin_crn = word_bin(len(bin_crn)) + bin_crn

        if len(bin_crn) < len(binary):
            return bin_crn, True

    return binary, False
     

### ---------------------------------------------------------------------------
### adds nibble
### ---------------------------------------------------------------------------
def nibble_add(nibble_last, nibble_new, adr_fix):
    if nibble_last > -1:
        binary = bytearray([nibble_last + nibble_new * 16]) + adr_fix
        adr_fix = bytearray(0)
        nibble_last = -1
    else:
        nibble_last = nibble_new
        binary = bytearray(0)
    return binary, nibble_last, adr_fix



### ---------------------------------------------------------------------------
### pack relocator table
### ---------------------------------------------------------------------------
def pack_reloc(binary):

    bin_reloc = bytearray(0)
    adr_last = -99999
    adr_fix = bytearray(0)
    nibble_last = -1

    for i in range(0, len(binary), 2):
        adr_new = word_get(binary[i:i+2])
        adr_dif = adr_new - adr_last
        if adr_dif < 2:
            print("## RELOC ERROR (DIF " + str(adr_dif) + ") AT " + str(i))
        if adr_dif > 16:
            nibble_new = 0
            adr_fix += binary[i:i+2]
        else:
            nibble_new = adr_dif - 1

        bin_add, nibble_last, adr_fix = nibble_add(nibble_last, nibble_new, adr_fix)
        bin_reloc += bin_add

        adr_last = adr_new

    if nibble_last > -1:
        adr_fix += bytearray(2)
        bin_add, nibble_last, adr_fix = nibble_add(nibble_last, 0, adr_fix)
        bin_reloc += bin_add
    else:
        bin_reloc += bytearray(3)

    bin_reloc += bytearray(len(bin_reloc) % 2)      # align to 2

    if len(bin_reloc) < len(binary):
        return bin_reloc, 2
    else:
        return binary, 0


### ---------------------------------------------------------------------------
### compress one EXE file
### ---------------------------------------------------------------------------
def compress_exe(file):

    print("Compressing " + file.upper() + "...")
    
    fil_ext = file[len(file) - 3:].lower()

    # load exe
    bin_exe = bin_load(file)

    exeid = bytearray()
    exeid.extend("SymExe10".encode())
    if bin_exe[48:48+8] != exeid:
        print("Not a SymbOS executable")
        print("")
        return
    if int(bin_exe[HD_FLAGS]) >= 16:
        print("File already compressed")
        print("")
        return

    # get area lengthes
    len_code = bin_exe[HD_FUL_CODE] + bin_exe[HD_FUL_CODE + 1] * 256
    len_data = bin_exe[HD_FUL_DATA] + bin_exe[HD_FUL_DATA + 1] * 256
    len_trns = bin_exe[HD_FUL_TRNS] + bin_exe[HD_FUL_TRNS + 1] * 256

    # calculate uncompressed areas
    unc_code = 0
    unc_data = 0
    unc_trns = 0

    if   fil_ext == "sav":
        unc_code = 3 + 16 * 40
    elif fil_ext == "wdg":
        unc_code = 6 + 4 * bin_exe[256+4]

    if bin_exe[HD_FLAGS] & 1 == 1:
        iconadr = word_get(bin_exe[HD_ICONOFS:HD_ICONOFS + 2])
        if iconadr == len_code:
            unc_data = 296
        elif iconadr == len_code + len_data:
            unc_trns = 296
        else:
            print("**bad Icon16 placement**")
            if iconadr < len_code + len_data:
                unc_data = -1
            else:
                unc_trns = -1

    # compress areas
    bin_code, flg_code = compress_area("code", unc_code, bin_exe[256:                len_code])
    bin_data, flg_data = compress_area("data", unc_data, bin_exe[len_code:           len_code + len_data])
    bin_trns, flg_trns = compress_area("trns", unc_trns, bin_exe[len_code + len_data:len_code + len_data + len_trns])
    bin_relc, flg_relp = pack_reloc(bin_exe[len_code + len_data + len_trns:])
    len_relc = len(bin_relc)
    bin_relc, flg_relc = compress_area("relc", 0, bin_relc)

    # update header
    bin_head = bytearray(bin_exe[:256])
    flags = int(bin_head[HD_FLAGS])
    if flg_code: flags += 128
    if flg_data: flags += 64
    if flg_trns: flags += 32
    if flg_relc: flags += 16
    if flg_relp: flags += 2
    bin_head[HD_FLAGS] = flags

    word_set(True, bin_head, HD_FUL_RELC, int(len_relc / 2))

    # save compressed exe
    run_cmd(f"ren {file} {file}.bak")
    bin_save(file, bin_head + bin_code + bin_data + bin_trns + bin_relc)

    len_org = len(bin_exe)
    len_crn = len(bin_head) + len(bin_code) + len(bin_data) + len(bin_trns) + len(bin_relc)
    print(f"DONE! compressed from {len_org} to {len_crn} ({len_crn/len_org*100:.0f}%)")
    print("")


### batch
files = glob.glob(sys.argv[1])
if len(files) == 0:
    print("File(s) not found")
else:
    for file in files:
        compress_exe(file)
