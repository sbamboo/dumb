import os,sys,base64,random,time,argparse,re,subprocess

from _helpers import *
import _libConUtils as lcu


def NULL(probe):
    print(probe)

def CONF(flag):
    pass

def LOCK(length):
    global STACKLEN
    STACKLEN = length+1

def FILL(hexchar):
    global STACK,STACK_CLEAR
    STACK_CLEAR = hexchar
    STACK = []
    for _ in range(STACKLEN):
        STACK.append(STACK_CLEAR)

def FAKE(pathindex):
    global STACK, STACKLEN, BUFFER_STACK
    path = REGI.get_blobstore_entry(BLOBSTORE,pathindex).decode(ENCODING)
    path = re.sub(r'[^\x20-\x7E]', '', path)
    path = os.path.abspath(path)
    if os.path.exists(path):
        TYPE,VERS,CONF,DATA,_ = readDumbFile(path)
        if VERS != COMP_FILEVER:
            raise ValueError("Incompatible version of file!")
        nstack = []
        for byte in DATA:
            nstack.append(byte)
        BUFFER_STACK = [*STACK]
        STACK = nstack
        STACKLEN = len(nstack)

def EXPR(pathindex):
    path = REGI.get_blobstore_entry(BLOBSTORE,pathindex).decode(ENCODING)
    TYPE =                        '0' # X
    VERS = format(COMP_FILEVER,'03b') # XXX
    CONF =                     '0000' # XXXX
    HEAD = binToByte(f"{TYPE}{VERS}{CONF}")
    DATA = bytes([HEAD,*STACK])
    path = re.sub(r'[^\x20-\x7E]', '', path)
    with open(path,'wb') as f:
        f.write(DATA)
        f.close()

def BACK():
    global STACK, STACKLEN, BUFFER_STACK
    STACK = [*BUFFER_STACK]
    STACKLEN = len(BUFFER_STACK)
    BUFFER_STACK = []

def INFO():
    fprint(
f"""DUMB {FRIENDLY_VERSION}, by Simon Kalmi Claesson
---------------------------------

DUMB uses a STACK for saving data,
aswell as RESULT which holds the result of the last operation,
and finally BLOBSTORE which contains 255 addressable content-slots that are pre-filled.
BLOBSTORE.0 usually is the internal registry.
BLOBSTORE.1 holds the internal RESULT.
BLOBSTORE.2 usually is parent to the interpriter.
BLOBSTORE.3 usually is parent to the file. (or if interactive same as above)
BLOBSTORE.4 usually is a preset file.
BLOBSTORE.5 usually is a preset file.

Methods are callable via their Hex-Adress or Name.

Interpriter Enviroment Properties:
  INTEP_INTERACTIVE = {INTEP_INTERACTIVE}
  ENCODING = {ENCODING}
  ENVIR_HEADER = {ENVIR_HEADER}
  COMP_FILEVER = {format(COMP_FILEVER,'04b')}
  STACK_CLEAR = {hex(STACK_CLEAR)}
  STACKLEN = {STACKLEN}
  CURRENT_VOID.len = {len(CURRENT_VOID) if CURRENT_VOID != None else 0}
  ITERATING_VOID = {ITERATING_VOID}
  ITERATING_INDEX = {ITERATING_INDEX}

Loaded methods: ({len(METHOD_ADDR_TO_FUNC.keys())}st)
{'\n'.join([f"  {intToHexByte(x['Addr'])}: {x['Name'].decode(ENCODING)} {' ('+METHOD_NAME_TO_DESC.get(x['Name'])+')' if METHOD_NAME_TO_DESC.get(x['Name']) != None else ''}" for x in REGI.getDecl(BLOBSTORE)])}
    """)

def POKE(pos,value):
    global STACK
    STACK[pos] = value

def WACK(pos):
    global STACK
    STACK[pos] = STACK_CLEAR

def SWAP(pos1,pos2):
    global STACK
    STACK[pos1] = STACK[pos2]
    tmp = STACK[pos2]
    STACK[pos1] = tmp

def WALK(pos1,pos2):
    if pos1 < len(STACK) and pos2 < len(STACK):
        set_result(bytes([*STACK][pos1:pos2+1]))

def MAXL():
    set_result(bytes([ len(get_result()) ]))

def PEEK(pos):
    set_result(bytes([ STACK[pos] ]))

def GRES(pos1,pos2):
    global STACK
    RESULT = get_result()
    if pos1 == pos2:
        pos2 = pos1+len(RESULT)
    BYTES = []
    if type(RESULT) in [tuple,list]:
        BYTES = RESULT
    elif type(RESULT) == bytes:
        if len(RESULT) > 1:
            BYTES = RESULT
        else:
            BYTES = [RESULT]
    if pos1 < len(STACK)-1:
        pos = pos1
        for byte in BYTES:
            if pos < len(STACK)-1 and pos <= pos2:
                STACK[pos] = byte
            pos +=1

def DICE(hexnumber1,hexnumber2):
    set_result(bytes([random.randint(hexnumber1,hexnumber2)]))

def TAKE():
    set_result(bytes(strToBytes(input(": "))))

def CRES():
    set_result(bytes([]))

def PRES():
    BYTES = get_result()
    STR = BYTES.decode(ENCODING)
    fprint(STR)

def LRES(pos):
    global STACK
    STACK[pos] = len(get_result())

def YEET():
    exit()

def WAIT(hex6_ms):
    time.sleep( round(hex6_ms / 1000) )

def VOID():
    global CURRENT_VOID
    CURRENT_VOID = []

def VEND(blobindex):
    if blobindex <= 0x05:
        raise Exception("VOID adressables must be more then 0x05!")
    global BLOBSTORE, CURRENT_VOID
    BYTES = bytes([])
    for x in CURRENT_VOID:
        BYTES = BYTES + bytes([0x17]) + safe_bytes(bytes([*x]))
    BYTES = BYTES.replace(bytes([0x17]),bytes([]),1)
    BLOBSTORE = REGI.set_blobstore_entry(BLOBSTORE,blobindex,safe_bytes(BYTES))
    CURRENT_VOID = None

def CALL(blobindex):
    raw = unsafe_bytes(REGI.get_blobstore_entry(BLOBSTORE,blobindex))
    lines = raw.split(bytes([0x17]))
    for line in lines:
        line = unsafe_bytes(line)
        exec_line(line)

def JPAT(pathindex1,pathindex2,pathindex3):
    if pathindex3 <= 0x05:
        raise Exception("PATH adressables must be more then 0x05!")
    global BLOBSTORE
    path1 = REGI.get_blobstore_entry(BLOBSTORE,pathindex1).decode(ENCODING)
    path2 = REGI.get_blobstore_entry(BLOBSTORE,pathindex2).decode(ENCODING)

    path3 = os.path.join(path1,path2)

    BLOBSTORE = REGI.set_blobstore_entry(BLOBSTORE,pathindex3,path3.encode(ENCODING))

def HACK():
    BYTES = get_result()
    STR = BYTES.decode(ENCODING)
    os.system(STR)

def ADDT(hexnumber1,hexnumber2):
    set_result(bytes([ hexnumber1+hexnumber2 ]))

def SUBT(hexnumber1,hexnumber2):
    set_result(bytes([ hexnumber1-hexnumber2 ]))

def MULT(hexnumber1,hexnumber2):
    set_result(bytes([ hexnumber1*hexnumber2 ]))

def DIVT(hexnumber1,hexnumber2):
    set_result(bytes([ abs(round(hexnumber1/hexnumber2)) ]))

def FLDT(hexnumber1,hexnumber2):
    set_result(bytes([ hexnumber1//hexnumber2 ]))

def POWT(hexnumber1,hexnumber2):
    set_result(bytes([ hexnumber1**hexnumber2 ]))

def MODT(hexnumber1,hexnumber2):
    set_result(bytes([ hexnumber1 % hexnumber2 ]))

def ADDS(pos1,pos2):
    set_result(bytes([ STACK[pos1]+STACK[pos2] ]))

def SUBS(pos1,pos2):
    set_result(bytes([ STACK[pos1]-STACK[pos2] ]))

def MULS(pos1,pos2):
    set_result(bytes([ STACK[pos1]*STACK[pos2] ]))

def DIVS(pos1,pos2):
    set_result(bytes([ abs(round(STACK[pos1]/STACK[pos2])) ]))

def FLDS(pos1,pos2):
    set_result(bytes([ STACK[pos1]//STACK[pos2] ]))

def POWS(pos1,pos2):
    set_result(bytes([ STACK[pos1]**STACK[pos2] ]))

def MODS(pos1,pos2):
    set_result(bytes([ STACK[pos1] % STACK[pos2] ]))

def TINT():
    #set_result(str(int(get_result())).encode(ENCODING))
    res = get_result()
    fin = bytes([])
    for byte in res:
        fin = fin + str(int(byte)).encode(ENCODING)
    set_result(fin)

def FINT():
    #set_result( bytes([ int(get_result().decode(ENCODING)) ]) )
    res = get_result()
    fin = bytes([])
    for byte in res:
        fin = fin + bytes([ int(bytes([byte]).decode(ENCODING)) ])
    set_result(fin)

def TBOL():
    #set_result(str(int(get_result())).encode(ENCODING))
    res = get_result()
    fin = bytes([])
    for byte in res:
        string = str(int(byte))
        if string == "1": string = "TRUE"
        elif string == "0": string = "FALSE"
        fin = fin + string.encode(ENCODING)
    set_result(fin)

def FBOL():
    #set_result( bytes([ int(get_result().decode(ENCODING)) ]) )
    res = get_result()
    fin = bytes([])
    chunks,rem = splitBytesInFourChunks(res)
    for chunk in chunks:
        string = chunk.decode(ENCODING)
        if string == "TRUE": string = "1"
        elif string == "FALSE": string = "0"
        fin = fin + bytes([ int(string) ])
    fin = fin + rem
    set_result(fin)

def REVS():
    global STACK
    STACK = reversed(STACK)

def IFIS(blobindex,pos1,pos2):
    if STACK[pos1] == STACK[pos2]:
        CALL(blobindex)

def IFNO(blobindex,pos1,pos2):
    if STACK[pos1] != STACK[pos2]:
        CALL(blobindex)

def IFGT(blobindex,pos1,pos2):
    if STACK[pos1] > STACK[pos2]:
        CALL(blobindex)

def IFLT(blobindex,pos1,pos2):
    if STACK[pos1] < STACK[pos2]:
        CALL(blobindex)

def FORP(blobindex,pos):
    # prep
    ITERATING_VOID = blobindex
    ITERATING_INDEX = 0
    # main
    times = STACK[pos]
    for _ in range(times):
        if ITERATING_VOID != None:
            CALL(ITERATING_VOID)
            ITERATING_INDEX += 1
        else:
            break
    # reset
    ITERATING_VOID = None
    ITERATING_INDEX = 0

def FORR(blobindex):
    # prep
    ITERATING_VOID = blobindex
    ITERATING_INDEX = 0
    # main
    times = get_result()[0]
    for _ in range(times):
        if ITERATING_VOID != None:
            CALL(ITERATING_VOID)
            ITERATING_INDEX += 1
        else:
            break
    # reset
    ITERATING_VOID = None
    ITERATING_INDEX = 0

def FORE(blobindex):
    # prep
    ITERATING_VOID = blobindex
    ITERATING_INDEX = 0
    # main
    times = len(get_result())
    for _ in range(times):
        if ITERATING_VOID != None:
            CALL(ITERATING_VOID)
            ITERATING_INDEX += 1
        else:
            break
    # reset
    ITERATING_VOID = None
    ITERATING_INDEX = 0

def WHIS(blobindex,pos1,pos2):
    # prep
    ITERATING_VOID = blobindex
    ITERATING_INDEX = 0
    # main
    while ITERATING_INDEX != None:
        if STACK[pos1] == STACK[pos2]:
            CALL(ITERATING_VOID)
            ITERATING_INDEX += 1
        else:
            break
    # reset
    ITERATING_VOID = None
    ITERATING_INDEX = 0

def WHNO(blobindex,pos1,pos2):
    # prep
    ITERATING_VOID = blobindex
    ITERATING_INDEX = 0
    # main
    while ITERATING_INDEX != None:
        if STACK[pos1] != STACK[pos2]:
            CALL(ITERATING_VOID)
            ITERATING_INDEX += 1
        else:
            break
    # reset
    ITERATING_VOID = None
    ITERATING_INDEX = 0

def WHGT(blobindex,pos1,pos2):
    # prep
    ITERATING_VOID = blobindex
    ITERATING_INDEX = 0
    # main
    while ITERATING_INDEX != None:
        if STACK[pos1] > STACK[pos2]:
            CALL(ITERATING_VOID)
            ITERATING_INDEX += 1
        else:
            break
    # reset
    ITERATING_VOID = None
    ITERATING_INDEX = 0

def WHLT(blobindex,pos1,pos2):
    # prep
    ITERATING_VOID = blobindex
    ITERATING_INDEX = 0
    # main
    while ITERATING_INDEX != None:
        if STACK[pos1] < STACK[pos2]:
            CALL(ITERATING_VOID)
            ITERATING_INDEX += 1
        else:
            break
    # reset
    ITERATING_VOID = None
    ITERATING_INDEX = 0

def BRCK():
    ITERATING_VOID = None
    ITERATING_INDEX = 0

def GETI():
    set_result(bytes([ITERATING_INDEX]))

def WPOK(_,pos1,*values):
    pos = pos1
    for v in values:
        if pos < len(STACK):
            STACK[pos] = v
        else:
            break
        pos += 1

def WPKR(_,pos1,*values):
    pos = pos1
    for v in values:
        if pos < len(STACK):
            STACK[pos] = v
        else:
            break
        pos += 1

def SWPB(blobindex1,blobindex2):
    if blobindex1 <= 0x05 or blobindex2 <= 0x05:
        raise Exception("SWAP adressables must be more then 0x05!")
    global BLOBSTORE
    bic1 = REGI.get_blobstore_entry(BLOBSTORE,blobindex1)
    bic2 = REGI.get_blobstore_entry(BLOBSTORE,blobindex2)
    BLOBSTORE = REGI.set_blobstore_entry(BLOBSTORE,blobindex1,bic2)
    BLOBSTORE = REGI.set_blobstore_entry(BLOBSTORE,blobindex2,bic1)

def SHFT(amnt):
    global STACK
    STACK = shiftList(STACK,amnt)

def USHT(amnt):
    global STACK
    STACK = unshiftList(STACK,amnt)

def SFTN(amnt):
    global STACK
    STACK = shiftListNonOverlap(STACK,amnt,STACK_CLEAR)

def UFTN(amnt):
    global STACK
    STACK = unshiftListNonOverlap(STACK,amnt,STACK_CLEAR)

def EXIS(pos,pathindex):
    path = REGI.get_blobstore_entry(BLOBSTORE,pathindex).decode(ENCODING)
    path = re.sub(r'[^\x20-\x7E]', '', path)
    if os.path.exists(path):
        STACK[pos] = 1
    else:
        STACK[pos] = 0

def EXIR(pathindex):
    path = REGI.get_blobstore_entry(BLOBSTORE,pathindex).decode(ENCODING)
    path = re.sub(r'[^\x20-\x7E]', '', path)
    if os.path.exists(path):
        set_result(bytes([1]))
    else:
        set_result(bytes([0]))

def REMA(pathindex):
    path = REGI.get_blobstore_entry(BLOBSTORE,pathindex).decode(ENCODING)
    path = re.sub(r'[^\x20-\x7E]', '', path)
    if os.path.exists(path):
        i = input(f"Are you sure you want to remove {os.path.basename(path)}? [Y/N] ")
        if i.strip().lower() == "y":
            os.remove(path)

def REMF(pathindex):
    path = REGI.get_blobstore_entry(BLOBSTORE,pathindex).decode(ENCODING)
    path = re.sub(r'[^\x20-\x7E]', '', path)
    if os.path.exists(path):
        os.remove(path)

def WRTE(pathindex):
    path = REGI.get_blobstore_entry(BLOBSTORE,pathindex).decode(ENCODING)
    path = re.sub(r'[^\x20-\x7E]', '', path)
    with open(path, 'wb') as f:
        BYTES = bytes([])
        for byte in STACK:
            BYTES = BYTES + bytes([byte])
        f.write(BYTES)
        f.close()

def WRTS(pathindex,pos1,pos2):
    path = REGI.get_blobstore_entry(BLOBSTORE,pathindex).decode(ENCODING)
    path = re.sub(r'[^\x20-\x7E]', '', path)
    if pos1 < len(STACK) and pos2 < len(STACK):
        with open(path, 'wb') as f:
            BYTES = bytes([])
            for byte in STACK[pos1:pos2+1]:
                BYTES = BYTES + bytes([byte])
            f.write(BYTES)
            f.close()

def WRTR(pathindex):
    path = REGI.get_blobstore_entry(BLOBSTORE,pathindex).decode(ENCODING)
    path = re.sub(r'[^\x20-\x7E]', '', path)
    with open(path, 'wb') as f:
        f.write(get_result())
        f.close()

def READ(blobindex,pathindex):
    global BLOBSTORE
    path = REGI.get_blobstore_entry(BLOBSTORE,pathindex).decode(ENCODING)
    path = re.sub(r'[^\x20-\x7E]', '', path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {os.path.basename(path)} is not found!")
    BYTES = bytes([])
    with open(path,'rb') as f:
        BYTES = f.read()
        f.close()
    BLOBSTORE = REGI.set_blobstore_entry(BLOBSTORE,blobindex,BYTES)

def REDR(pathindex):
    global BLOBSTORE
    path = REGI.get_blobstore_entry(BLOBSTORE,pathindex).decode(ENCODING)
    path = re.sub(r'[^\x20-\x7E]', '', path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {os.path.basename(path)} is not found!")
    BYTES = bytes([])
    with open(path,'rb') as f:
        BYTES = f.read()
        f.close()
    set_result(BYTES)

def APEW(pathindex):
    path = REGI.get_blobstore_entry(BLOBSTORE,pathindex).decode(ENCODING)
    path = re.sub(r'[^\x20-\x7E]', '', path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {os.path.basename(path)} is not found!")
    with open(path, 'ab') as f:
        BYTES = bytes([])
        for byte in STACK:
            BYTES = BYTES + bytes([byte])
        f.write(BYTES)
        f.close()

def APES(pathindex,pos1,pos2):
    path = REGI.get_blobstore_entry(BLOBSTORE,pathindex).decode(ENCODING)
    path = re.sub(r'[^\x20-\x7E]', '', path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {os.path.basename(path)} is not found!")
    if pos1 < len(STACK) and pos2 < len(STACK):
        with open(path, 'ab') as f:
            BYTES = bytes([])
            for byte in STACK[pos1:pos2+1]:
                BYTES = BYTES + bytes([byte])
            f.write(BYTES)
            f.close()

def APER(pathindex):
    path = REGI.get_blobstore_entry(BLOBSTORE,pathindex).decode(ENCODING)
    path = re.sub(r'[^\x20-\x7E]', '', path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {os.path.basename(path)} is not found!")
    with open(path, 'ab') as f:
        f.write(get_result)
        f.close()

def EVAL():
    exec_byte_inp(get_result(),False)

def ARGS():
    pass

def REPL(value1,value2):
    global STACK
    for i,x in enumerate(STACK):
        if x == value1:
            STACK[i] = value2

def REPR(value1,value2):
    fin = bytes([])
    for i,byte in get_result():
        if byte == value1:
            fin = fin + bytes([value2])
        else:
            fin = fin + bytes([byte])
    set_result(fin)

def DELE(value):
    global STACK
    for i,x in enumerate(STACK):
        if x == value:
            STACK[i] = STACK_CLEAR

def DELR(value):
    fin = bytes([])
    for i,byte in get_result():
        if byte != value:
            fin = fin + bytes([byte])
    set_result(fin)

def FIND(value):
    indexes = []
    for i,x in enumerate(STACK):
        if x == value:
            indexes.append(i)
    set_result( bytes(indexes) )

def FINO(value):
    index = None
    for i,x in enumerate(STACK):
        if x == value:
            index = i
            break
    if index != None:
        set_result( bytes([index]) )


FRIENDLY_VERSION = "0.0"
ENCODING = "ascii"
ENVIR_HEADER = None
COMP_FILEVER = 0b0000
STACK_CLEAR = 0x00
BUFFER_STACK = []
STACK = []
CURRENT_VOID = None
ITERATING_VOID = None
ITERATING_INDEX = 0
BLOBSTORE = bytes([
    0x17, 0b10_000000,
#   ^ETB  ^REG-^conf^
          0x00, 0x4E,0x55,0x4C,0x4C, 0b0000_0001, 0x00,
#         ^i=0  ^Decl.Name=NULL---^  ^type+len-^  ^param
          0x00, 0x43,0x4F,0x4E,0x46, 0b0000_0001, 0x00,
#         ^i=0  ^Decl.Name=CONF---^  ^type+len-^  ^param
    0x17, 0b11_000000,
#   ^ETB  ^RES-^conf^
    0x17, 0b00_000000, *strToBytes(os.path.dirname(os.path.abspath(__file__))),
#   ^ETB  ^PAT-^conf^  ^ParentDirToInterpriter
    0x17, 0b00_000000, *strToBytes(os.path.dirname(os.path.abspath(__file__))),
#   ^ETB  ^PAT-^conf^  ^ParentDirToExecFile
    0x17, 0b00_000000, *strToBytes("stack.dumb"),
#   ^ETB  ^PAT-^conf^  ^File1
    0x17, 0b00_000000, *strToBytes("stack2.dumb"),
#   ^ETB  ^PAT-^conf^  ^File1
])
STACKLEN = 0
REGI_tttttttt = None
INPUT_TYPE_FRIENDLY_TO_INDEX = {
    "NONE": 0,
    "ONLY": 1,
    "RNGE": 2,
    "FROM": 3,
}
PARAMTYPE_FRIENDLY_TO_INDEX = {
    "UNKNOWN":   0,
    "HEXx":      1,
    "HEX":       2,
    "HEX1":      3,
    "HEX2":      4,
    "HEX4":      5,
    "HEX6":      6,
    "HEX8":      7,
    "CHAR":      8,
    "HEXCHAR":   9,
    "HEXNUMBER": 10,
    "NUMBER":    11,
    "BLOBINDEX": 12,
    "PATHINDEX": 13,
    "*":         14,
    "POS*":      15,
}
METHOD_ADDR_TO_FUNC = {
    0x00: NULL
}
METHOD_NAME_TO_DESC = {}
DYNAMIC_PARAM_METHODS = []
DYNAMIC_PARAM_METHODS_POSLEN = []



class REGI():
    @staticmethod
    def split_blobstore(blobstore):
        return split_bytes_by_delimiter(blobstore)[1:]
    @staticmethod
    def ensure_blobstore_adresses(blobstore):
        split = split_bytes_by_delimiter(blobstore)
        l = len(split)-1
        for _ in range(256-l):
            blobstore = blobstore + bytes([0x17])
        return blobstore
    @staticmethod
    def truncate_blobstore_empties(blobstore):
        split = split_bytes_by_delimiter(blobstore)
        furthest_non_empty = 0
        for i,part in enumerate(split[1:]):
            if part != b'':
                furthest_non_empty = i
        new = bytes([])
        for p in split[:furthest_non_empty+2]:
            new = new + bytes([0x17]) + p
        return new.replace(bytes([0x17]),bytes([]),1)
    @staticmethod
    def join_blobstore_split(split):
        return bytes([0x17]).join(split)
    @staticmethod
    def set_blobstore_entry(blobstore,index,newbytes):
        split = split_bytes_by_delimiter(blobstore)
        split[index+1] = newbytes
        return REGI.join_blobstore_split(split)
    @staticmethod
    def get_blobstore_entry(blobstore,index):
        split = split_bytes_by_delimiter(blobstore)
        return split[index+1]
    @staticmethod
    def get(blobstore):
        '''RETURNS (<regiConfig>,<regi>)'''
        split = REGI.split_blobstore(blobstore)
        for blob in split:
            # REGI
            if len(blob) == 1:
                return blob[0],[]
            if len(blob) > 1:
                if byteToBinStr(blob[0]).startswith("10"):
                    return blob[0],blob[1:]
    @staticmethod
    def append(blobstore,newbytes) -> bytes:
        split = REGI.split_blobstore(blobstore)
        nbytes = bytes([])
        # Find regi
        for blob in split:
            if len(blob) > 1:
                if byteToBinStr(blob[0]).startswith("10"):
                    nbytes = nbytes + bytes([0x17]) + blob + newbytes
                else:
                    nbytes = nbytes + bytes([0x17]) + blob
            else:
                nbytes = nbytes + bytes([0x17]) + blob
        return nbytes
    
    @staticmethod
    def clear(blobstore) -> bytes:
        split = REGI.split_blobstore(blobstore)
        nbytes = bytes([])
        # Find regi
        for blob in split:
            if len(blob) > 1:
                if byteToBinStr(blob[0]).startswith("10"):
                    nbytes = nbytes + bytes([0x17, blob[0]])
                else:
                    nbytes = nbytes + bytes([0x17]) + blob
            else:
                nbytes = nbytes + bytes([0x17]) + blob
        return nbytes

    @staticmethod
    def decl(blobstore, name,inputtype,paramtypes:list,paramlength="auto",method=None,methodpair=METHOD_ADDR_TO_FUNC):
        if len(name) != 4:
            raise ValueError("DECL.NAME must be 4 chars long!")
        if type(inputtype) == str:
            if inputtype not in INPUT_TYPE_FRIENDLY_TO_INDEX.keys():
                raise ValueError(f"DECL.INPUTTYPE must be an int between 0 and 15 or one of {list(INPUT_TYPE_FRIENDLY_TO_INDEX.keys())}")
            else:
                inputtype = INPUT_TYPE_FRIENDLY_TO_INDEX[inputtype]
        elif type(inputtype) == int:
            if inputtype > 0 or inputtype < len(INPUT_TYPE_FRIENDLY_TO_INDEX.keys()):
                pass
            else:
                raise ValueError(f"DECL.INPUTTYPE must be an int between 0 and {len(INPUT_TYPE_FRIENDLY_TO_INDEX.keys())-1} (incl) or one of {list(INPUT_TYPE_FRIENDLY_TO_INDEX.keys())}")
        else:
            raise ValueError(f"DECL.INPUTTYPE must be an int between 0 and {len(INPUT_TYPE_FRIENDLY_TO_INDEX.keys())-1} (incl) or one of {list(INPUT_TYPE_FRIENDLY_TO_INDEX.keys())}")
        if paramlength == "auto":
            paramlength = len(paramtypes)
        if type(paramlength) == int:
            if paramlength > 0 or paramlength < 16:
                pass
            else:
                raise ValueError(f"DECL.PARAMLENGTH must be an int between 0 and 15")
        else:
            raise ValueError(f"DECL.PARAMLENGTH must be an int between 0 and 15")
        n_paramtypes = []
        if type(paramtypes) not in [tuple,list]: 
            raise ValueError("ParamTypes must be either tuple or list!")
        for x in paramtypes:
            if type(x) == str:
                if x not in PARAMTYPE_FRIENDLY_TO_INDEX.keys():
                    raise ValueError(f"DECL.PARAMTYPE must be an int between 0 and {len(PARAMTYPE_FRIENDLY_TO_INDEX.keys())-1} (incl) or one of {list(PARAMTYPE_FRIENDLY_TO_INDEX.keys())}")
                else:
                    n_paramtypes.append( PARAMTYPE_FRIENDLY_TO_INDEX[x] )
            elif type(x) == int:
                if x > 0 or x < len(PARAMTYPE_FRIENDLY_TO_INDEX.keys()):
                    n_paramtypes.append( PARAMTYPE_FRIENDLY_TO_INDEX[x] )
                else:
                    raise ValueError(f"DECL.PARAMTYPE must be an int between 0 and {len(PARAMTYPE_FRIENDLY_TO_INDEX.keys())-1} (incl) or one of {list(PARAMTYPE_FRIENDLY_TO_INDEX.keys())}")
            else:
                raise ValueError(f"DECL.PARAMTYPE must be an int between 0 and {len(PARAMTYPE_FRIENDLY_TO_INDEX.keys())-1} (incl) or one of {list(PARAMTYPE_FRIENDLY_TO_INDEX.keys())}")

        LEN = len(REGI.getDecl_raw(blobstore))
        ADRESS = LEN
        if ADRESS > 0x16:
            ADRESS += 1
        if inputtype == 3:
            if PARAMTYPE_FRIENDLY_TO_INDEX["*"] in n_paramtypes:
                DYNAMIC_PARAM_METHODS.append(ADRESS)
            elif PARAMTYPE_FRIENDLY_TO_INDEX["POS*"] in n_paramtypes:
                DYNAMIC_PARAM_METHODS_POSLEN.append(ADRESS)
        DECL_NAME = strToBytes(name)
        DECL_BYTES = bytes([ADRESS, *DECL_NAME, binToByte(intToBinaryStr(inputtype,4)+intToBinaryStr(paramlength,4)), *n_paramtypes])
        if methodpair != None and method != None:
            methodpair[ADRESS] = method

        ret = REGI.append(BLOBSTORE,DECL_BYTES)
        return ret
    
    @staticmethod
    def getDecl_raw(blobstore):
        b = REGI.get(blobstore)
        if b == None: return []
        regio,regi = b


        parsed_segments = []
        index = 0
        
        while index < len(regi):
            # Start of a segment
            start_index = index
            
            # Skip the address (1 byte) and name (4 bytes)
            index += 1 + 4
            
            # Parse the config byte (1 byte) and extract content length (last 4 bits)
            config_byte = regi[index]
            bs = byteToBinStr(config_byte)
            content_length = int(bs[4:], 2)
            index += 1
            
            # Skip content bytes (length from the config byte)
            index += content_length
            
            # Extract the full segment as raw bytes and append it
            parsed_segments.append(regi[start_index:index])
        return parsed_segments

    @staticmethod
    def getDecl(blobstore,methodpair=METHOD_ADDR_TO_FUNC):
        p = REGI.getDecl_raw(blobstore)
        toret = []
        for x in p:
            bs = byteToBinStr(x[5])
            d = {
                "Addr": x[0],
                "Name": x[1:5],
                "Type": int(bs[:4],2),
                "Length": int(bs[4:],2),
                "Content": x[6:]
            }
            if methodpair != None:
                if x[0] in methodpair.keys():
                    d["Method"] = methodpair[x[0]]
            toret.append(d)
        return toret

    @staticmethod
    def getDecl_bname(blobstore,name,methodpair=METHOD_ADDR_TO_FUNC):
        disp = REGI.getDecl(blobstore,methodpair)
        if disp != None:
            for x in disp:
                xname = name
                aname = name
                try:
                    xname = int(name,16)
                except: pass
                try:
                    aname = name.encode(ENCODING)
                except: pass
                if x["Addr"] == name:
                    return x
                elif x["Addr"] == xname:
                    return x
                elif x["Name"] == name:
                    return x
                elif x["Name"] == aname:
                    return x

def safe_bytes(bytedata):
    return base64.b64encode(bytedata)

def unsafe_bytes(bytedata):
    return base64.b64decode(bytedata)

def get_result():
    return unsafe_bytes(REGI.get_blobstore_entry(BLOBSTORE,0x01))

def set_result(binarydata):
    global BLOBSTORE
    BLOBSTORE = REGI.set_blobstore_entry(BLOBSTORE,0x01,safe_bytes(binarydata))

def declFast(cmds):
    global BLOBSTORE
    for c in cmds:
        if callable(c[-1]):
            BLOBSTORE = REGI.decl(BLOBSTORE,*c[:-1],method=c[-1])
        else:
            BLOBSTORE = REGI.decl(BLOBSTORE,*c[:-2],method=c[-2])
            METHOD_NAME_TO_DESC[c[0].encode(ENCODING)] = c[-1]

def addr_to_int(addrStr,retType=False):
    """
    retType == False:
        -> <int>
    retType == True:
        -> (<mode>,<int>)
    mode.0 : HEX
    mode.1 : StackPos
    mode.2 : BlobIndex
    mode.3 : BlobIndex (as-path)
    """
    addrStr = addrStr.strip()
    if retType == True:
        if addrStr.startswith("0x"):
            return 0,int(addrStr,16)
        elif addrStr.startswith("Px"):
            return 1,int(addrStr.replace("Px","0x",1),16)
        elif addrStr.startswith("Ix"):
            return 2,int(addrStr.replace("Ix","0x",1),16)
        elif addrStr.startswith("Sx"):
            return 3,int(addrStr.replace("Sx","0x",1),16)
    else:
        if addrStr.startswith("0x"):
            return int(addrStr,16)
        elif addrStr.startswith("Px"):
            return int(addrStr.replace("Px","0x",1),16)
        elif addrStr.startswith("Ix"):
            return int(addrStr.replace("Ix","0x",1),16)
        elif addrStr.startswith("Sx"):
            return int(addrStr.replace("Sx","0x",1),16)

def readDumbFile(fullAbsPath):
    if os.path.exists(fullAbsPath):
        binary = bytes([])
        with open(fullAbsPath, "rb") as f:
            binary = f.read()
            f.close()
        HEAD = byteToBinStr(binary[0])
        TYPE = int(HEAD[0])     # X
        VERS = int(HEAD[1:4],2) # XXX
        CONF = int(HEAD[4:],2)  # XXXX
        DATA = binary[1:]

        # check
        if VERS != COMP_FILEVER:
            raise ValueError("Incompatible version of file!")

        # CODE
        if TYPE == 0:
            CODE = bytes([])
            BLOB = bytes([])
            hf_0x17 = False
            for byte in DATA:
                if byte == 0x17:
                    hf_0x17 = True
                if hf_0x17 == False:
                    CODE = CODE + bytes([byte])
                else:
                    BLOB = BLOB + bytes([byte])
            return TYPE,VERS,CONF,CODE,BLOB
        # STACK
        if TYPE == 1:
            return TYPE,VERS,CONF,DATA,None

def exec_line(bytesline):
    global BLOBSTORE, FOUND_VEND_ADDR
    if CURRENT_VOID != None:
        if FOUND_VEND_ADDR != None:
            if bytesline[0] != FOUND_VEND_ADDR:
                CURRENT_VOID.append(bytesline)
                return

    CMDD = REGI.getDecl_bname(BLOBSTORE,bytesline[0])
    if CMDD.get("Method") != None:
        if len(bytesline[1:]) >= 1:
            try:
                CMDD["Method"](*bytesline[1:])
            except TypeError as e:
                print(e)
        else:
            try:
                CMDD["Method"]()
            except TypeError as e:
                print(e)
    else:
        print(f"$ {REGI.getDecl_bname(BLOBSTORE,bytesline[0])['Name']} < {bytesline[1:]}")

def exec_conf_line(line):
    if line.strip() == ".clear":
        lcu.clear()

def combine_byte_file(HEAD,EXEC,BLOBp,REGIp):
    # config 0001 has no REGI included
    if byteToBinStr(HEAD[0])[-4:].endswith("01"):
        # Reset REGISTRY
        BLOBSTORE2 = REGI.set_blobstore_entry(BLOBSTORE,0x00,bytes([0b10_000000]))
        # Reset Ix02,Ix03,Ix04,Ix05
        BLOBSTORE2 = REGI.set_blobstore_entry(BLOBSTORE2,0x02,bytes([0b00_000000]))
        BLOBSTORE2 = REGI.set_blobstore_entry(BLOBSTORE2,0x03,bytes([0b00_000000]))
        BLOBSTORE2 = REGI.set_blobstore_entry(BLOBSTORE2,0x04,bytes([0b00_000000]))
        BLOBSTORE2 = REGI.set_blobstore_entry(BLOBSTORE2,0x05,bytes([0b00_000000]))
        # Append REGIp
        if len(REGIp) > 0: BLOBSTORE2 = REGI.append(BLOBSTORE2)
        # Combine
        BLOBSTORE2 = REGI.truncate_blobstore_empties(BLOBSTORE2)
        return bytes([*HEAD,*EXEC,*BLOBSTORE2,*BLOBp])

    # config 0010 has no BLOBSTORE at al
    elif byteToBinStr(HEAD[0])[-4:].endswith("10"):
        # Reset Ix02,Ix03,Ix04,Ix05
        # Combine
        return bytes([*HEAD,*EXEC])

    # others have REGI included
    else:
        BLOBSTORE2 = BLOBSTORE
        # Reset Ix02,Ix03,Ix04,Ix05
        BLOBSTORE2 = REGI.set_blobstore_entry(BLOBSTORE2,0x02,bytes([0b00_000000]))
        BLOBSTORE2 = REGI.set_blobstore_entry(BLOBSTORE2,0x03,bytes([0b00_000000]))
        BLOBSTORE2 = REGI.set_blobstore_entry(BLOBSTORE2,0x04,bytes([0b00_000000]))
        BLOBSTORE2 = REGI.set_blobstore_entry(BLOBSTORE2,0x05,bytes([0b00_000000]))
        # Append REGIp
        if len(REGIp) > 0: BLOBSTORE2 = REGI.append(BLOBSTORE2,bytes(REGIp))
        # Combine
        BLOBSTORE2 = REGI.truncate_blobstore_empties(BLOBSTORE2)
        return bytes([*HEAD,*EXEC,*BLOBSTORE2,*BLOBp])


# MARK: Define
declFast([
    ["LOCK","ONLY",["HEXNUMBER"],LOCK,"Locks the STACKLEN to X."],
    ["FILL","ONLY",["HEXCHAR"],FILL,"Fills the stack with STACKLEN of X."],
    ["FAKE","ONLY",["PATHINDEX"],FAKE,"Imports a STACK from path A"],
    ["EXPR","ONLY",["PATHINDEX"],EXPR,"Exports the STACK to path A."],
    ["BACK","NONE",[],BACK,"Resets to default STACK."],

    ["INFO","NONE",[],INFO,"Shows this info."],

    ["POKE","ONLY",["HEXx","HEX"],POKE,"Puts value X at STACK.a"],
    ["WACK","ONLY",["HEXx"],WACK,"Clears the value at STACK.a"],
    ["SWAP","ONLY",["HEXx","HEXx"],SWAP,"Swaps the values at STACK.a and STACK.b"],

    ["WALK","ONLY",["HEXx","HEXx"],WALK,"Gets the stack values from STACK.a to STACK.b"],
    ["MAXL","NONE",[],MAXL,"Gets the locked lenght of stack."],
    ["PEEK","ONLY",["HEXx"],PEEK,"Gets the value at STACK.a"],
    ["GRES","ONLY",["HEXx","HEXx"],GRES,"RESULT into STACK starting at A until B, if A==B, until end-of-RESULT or end-of-STACK."],

    ["DICE","ONLY",["HEXNUMBER","HEXNUMBER"],DICE,"Gives random betwen A and B, inclusive."],
    ["TAKE","NONE",[],TAKE,"Asks the user for text input."],

    ["CRES","NONE",[],CRES,"Clears RESULT."],
    ["PRES","NONE",[],PRES,f"Prints the content of RESULT as {ENCODING}."],
    ["LRES","ONLY",["HEXx"],LRES,"Gets the length of RESULT."],

    ["YEET","NONE",[],YEET,"Exits."],
    ["WAIT","ONLY",["HEX6"],WAIT,"Waits for X ms."],

    ["VOID","NONE",[],VOID,"Starts a VOID."],
    ["VEND","ONLY",["BLOBINDEX"],VEND,"Closes the current VOID to an adress, at lteast 0x06."],
    ["CALL","ONLY",["BLOBINDEX"],CALL,"Calls a VOID, adressables at least 0x06."],
    ["JPAT","ONLY",["PATHINDEX","PATHINDEX","PATHINDEX"],JPAT,"Joins the paths in A and B to C."],
    ["HACK","NONE",[],HACK,"Sends RESULT to cli and captures stdout."],

    ["ADDT","ONLY",["HEXNUMBER","HEXNUMBER"],ADDT,"Calculates a + b"],
    ["SUBT","ONLY",["HEXNUMBER","HEXNUMBER"],SUBT,"Calculates a - b"],
    ["MULT","ONLY",["HEXNUMBER","HEXNUMBER"],MULT,"Calculates a * b"],
    ["DIVT","ONLY",["HEXNUMBER","HEXNUMBER"],DIVT,"Calculates a / b, abs+round"],
    ["FLDT","ONLY",["HEXNUMBER","HEXNUMBER"],FLDT,"Calculates a // b"],
    ["POWT","ONLY",["HEXNUMBER","HEXNUMBER"],POWT,"Calculates a ^ b"],
    ["MODT","ONLY",["HEXNUMBER","HEXNUMBER"],MODT,"Calculates a % b"],

    ["ADDS","ONLY",["HEXx","HEXx"],ADDS,"Calculates STACK.a + STACK.b"],
    ["SUBS","ONLY",["HEXx","HEXx"],SUBS,"Calculates STACK.a - STACK.b"],
    ["MULS","ONLY",["HEXx","HEXx"],MULS,"Calculates STACK.a * STACK.b"],
    ["DIVS","ONLY",["HEXx","HEXx"],DIVS,"Calculates STACK.a / STACK.b, abs+round"],
    ["FLDS","ONLY",["HEXx","HEXx"],FLDS,"Calculates STACK.a // STACK.b"],
    ["POWS","ONLY",["HEXx","HEXx"],POWS,"Calculates STACK.a ^ STACK.b"],
    ["MODS","ONLY",["HEXx","HEXx"],MODS,"Calculates STACK.a % STACK.b"],

    ["TINT","NONE",[],TINT,"Interprites the RESULT to INT placed to RESULT"],
    ["FINT","NONE",[],FINT,"Interprites the RESULT from INT placed to RESULT."],
    ["TBOL","NONE",[],TBOL,"Interprites the RESULT to BOOL placed to RESULT."],
    ["FBOL","NONE",[],FBOL,"Interprites the RESULT from BOOL placed to RESULT."],

    ["REVS","NONE",[],REVS,"Reverses the stack."],

    ["IFIS","ONLY",["BLOBINDEX","HEXx","HEXx"],IFIS,"Calls if STACK.a == STACK.b"],
    ["IFNO","ONLY",["BLOBINDEX","HEXx","HEXx"],IFNO,"Calls if STACK.a != STACK.b"],
    ["IFGT","ONLY",["BLOBINDEX","HEXx","HEXx"],IFGT,"Calls if STACK.a > STACK.b"],
    ["IFLT","ONLY",["BLOBINDEX","HEXx","HEXx"],IFLT,"Calls if STACK.a < STACK.b"],

    ["FORP","ONLY",["BLOBINDEX","HEXx"],FORP,"Iterates STACK.a times."],
    ["FORE","ONLY",["BLOBINDEX"],FORE,"Iterates for each entry in RESULT."],
    ["FORR","ONLY",["BLOBINDEX"],FORR,"Iterates RESULT times."],

    ["WHIS","ONLY",["BLOBINDEX","HEXx","HEXx"],WHIS,"While STACK.a == STACK.b"],
    ["WHNO","ONLY",["BLOBINDEX","HEXx","HEXx"],WHNO,"While STACK.a != STACK.b"],
    ["WHGT","ONLY",["BLOBINDEX","HEXx","HEXx"],WHGT,"While STACK.a > STACK.b"],
    ["WHLT","ONLY",["BLOBINDEX","HEXx","HEXx"],WHLT,"While STACK.a < STACK.b"],

    ["BRCK","NONE",[],BRCK,"Breaks interation."],
    ["GETI","NONE",[],GETI,"Gets iter-index to result."],

    ["WPOK","FROM",["HEX","HEXx","*"],WPOK,"Pokes X values into STACK starting at POS. (PARAM-LEN FIRST!)"],
    ["WPKR","FROM",["HEXx","HEXx","POS*"],WPKR,"Pokes the value from STACK at POS1 into STACK starting at POS2. (POS to PARAM-LEN FIRST!)"],

    ["SWPB","ONLY",["HEXx","HEXx"],SWPB,"Swaps the content of two BLOBSTORE addresses."],

    ["SHFT","ONLY",["HEX"],SHFT,"Shifts the stack forwards by A"],
    ["USHT","ONLY",["HEX"],USHT,"unshifts the stack forwards by A"],
    ["SFTN","ONLY",["HEX"],SFTN,"Shifts the stack forwards by A"],
    ["UFTN","ONLY",["HEX"],UFTN,"unshifts the stack forwards by A"],

    ["EXIS","ONLY",["HEXx","PATHINDEX"],EXIS,"Saves 0 or 1 to POS if BLOBINDEX exists."],
    ["EXIR","ONLY",["PATHINDEX"],EXIR,"Saves 0 or 1 to RESULT if BLOBINDEX exists."],
    ["REMA","ONLY",["PATHINDEX"],REMA,"Removes the file. Asks if sure"],
    ["REMF","ONLY",["PATHINDEX"],REMF,"Removes the file. Just removes"],
    ["WRTE","ONLY",["PATHINDEX"],WRTE,"Writes the stack to a file as raw bytes."],
    ["WRTS","ONLY",["PATHINDEX","HEXx","HEXx"],WRTS,"Writes the stack between two indexes to a file as raw bytes."],
    ["WRTR","ONLY",["PATHINDEX"],WRTR,"Writes the RESULT to a file at a filepath as raw bytes."],
    ["READ","ONLY",["BLOBINDEX","PATHINDEX"],READ,"Puts into BLOBINDEX the content from a filepath."],
    ["REDR","ONLY",["PATHINDEX"],REDR,"Puts into RESULT the content from a file from a filepath."],
    ["APEW","ONLY",["PATHINDEX"],APEW,"Appends the STACK to a file from a filepath."],
    ["APES","ONLY",["PATHINDEX","HEXx","HEXx"],APES,"Appends the STACK between two indexes to a file from filepath."],
    ["APER","ONLY",["PATHINDEX"],APER,"Appends the RESULT to a file from a filepath."],

    ["EVAL","NONE",[],EVAL,"Evaluates RESULT as binary-source."],

    ["ARGS","NONE",[],ARGS,"Puts any CLI params into RESULT as a list."],

    ["REPL","ONLY",["HEX","HEX"],REPL,"Replaces every instance of A in the stack with B."],
    ["REPR","ONLY",["HEX","HEX"],REPL,"Replaces every instance of A in RESULT with B."],
    ["DELE","ONLY",["HEX"],DELE,"Empties every instance of A in the stack."],
    ["DELR","ONLY",["HEX"],DELR,"Empties every instance of A in RESULT."],
    ["FIND","ONLY",["HEX"],FIND,"Returns al the indexes where A is in the stack to RESULT as a list."],
    ["FINO","ONLY",["HEX"],FINO,"Returns fhe first index where A is in the stack to RESULT."],
])

# MARK: InterpFuncs
def exec_cli_input(inp,retbytes=False):
    if ";" in inp:
        inps = [x.strip() for x in inp.split(";")]
    else:
        inps = [inp.strip()]
    for inp in inps:
        if inp.startswith("."):
            exec_conf_line(inp)
        elif not inp.startswith("#"):
            if "#" in inp:
                inp = inp.split("#")[0].rstrip()
            WORD = inp[:4]
            if WORD in ["0x17",0x17]:
                fprint("{f.red}ERROR: 0x17 is not addressable!{r}")
            else:
                CMDD = REGI.getDecl_bname(BLOBSTORE,WORD)
                if CMDD == None:
                    fprint("{f.red}ERROR: Command "+WORD+" is not defined!{r}")
                else:
                    rest = inp[4:].lstrip()
                    if "," in rest:
                        args = [addr_to_int(x) for x in rest.split(",")]
                    else:
                        args = [addr_to_int(x) for x in rest.split(" ")]
                    if None in args: args.remove(None)
                    line = bytes([CMDD["Addr"],*args])
                    if retbytes == True:
                        return line
                    else:
                        exec_line(line)

def exec_byte_inp(EXEC,retbytes=False):
    bytelines = []
    WORDd = None
    traversed = 0
    args = []
    found_dyn_param_len_byte = 0
    for bytei,byte in enumerate(EXEC):
        if WORDd == None:
            WORDd = byte
            if type(WORDd) == bytes:
                if len(WORDd) > 0: WORDd = WORDd[0]
            if WORDd in ["0x17",0x17]:
                fprint("{f.red}ERROR: 0x17 is not addressable!{r}")
                exit()
            
            CMDD = REGI.getDecl_bname(BLOBSTORE,WORDd)

            if CMDD == None:
                intep_debug_print("{f.red}CMD: "+hex(byte)+" NONE{r}")
                if byte in ["0x17",0x17,bytes([0x17])]:
                    fprint("{f.red}ERROR: 0x17 is not addressable!{r}")
                exit()
            else:
                WORDd = CMDD
                intep_debug_print("{f.green}CMD: "+hex(byte)+" '"+WORDd['Name'].decode(ENCODING)+"'{r}")

            MAXLEN = WORDd["Length"]

            if type(WORDd) == dict:
                if MAXLEN == 0:
                    # exec
                    intep_debug_print("{f.blue}EXE: "+hex(WORDd['Addr'])+" {f.yellow}(NO_PARAMS){r}")
                    try:
                        if retbytes == True:
                            bytelines.append( bytes([WORDd["Addr"]]) )
                        else:
                            exec_line( bytes([WORDd["Addr"]]) )
                    except Exception as e:
                        fprint("{f.red}ERROR: "+e+"{r}")
                    # reset
                    traversed = 0
                    WORDd = None
                    args = []
                    found_dyn_param_len_byte = 0

                elif bytei == len(EXEC)-1:
                    fprint("{f.red}ERROR: "+hex(WORDd['Addr'])+" takes "+str(WORDd['Length'])+" params, but none where given!{r}")
                    exit()

        else:
            intep_debug_print("{f.magenta}ARG: "+hex(byte)+"{r}")

            MAXLEN = WORDd["Length"]

            if WORDd["Addr"] in DYNAMIC_PARAM_METHODS:
                if found_dyn_param_len_byte == 0:
                    MAXLENt = byte
                    # Add the amount of non-dynamic args to the length
                    star = PARAMTYPE_FRIENDLY_TO_INDEX["*"]
                    posstar = PARAMTYPE_FRIENDLY_TO_INDEX["POS*"]
                    WORDd_args = [*WORDd["Content"]]
                    if star in WORDd_args:
                        WORDd_args.remove(star)
                        MAXLENt += len(WORDd_args)
                    elif posstar in WORDd_args:
                        WORDd_args.remove(posstar)
                        MAXLENt += len(WORDd_args)
                    found_dyn_param_len_byte = MAXLENt
                MAXLEN = found_dyn_param_len_byte

            elif WORDd["Addr"] in DYNAMIC_PARAM_METHODS_POSLEN:
                if found_dyn_param_len_byte == 0:
                    byte = STACK[byte]
                    MAXLENt = byte
                    # Add the amount of non-dynamic args to the length
                    star = PARAMTYPE_FRIENDLY_TO_INDEX["*"]
                    posstar = PARAMTYPE_FRIENDLY_TO_INDEX["POS*"]
                    WORDd_args = [*WORDd["Content"]]
                    if star in WORDd_args:
                        WORDd_args.remove(star)
                        MAXLENt += len(WORDd_args)
                    elif posstar in WORDd_args:
                        WORDd_args.remove(posstar)
                        MAXLENt += len(WORDd_args)
                    found_dyn_param_len_byte = MAXLENt
                MAXLEN = found_dyn_param_len_byte

            if traversed < MAXLEN-1:
                args.append(byte)
                traversed += 1
            else:
                args.append(byte)
                # exec
                intep_debug_print("{f.blue}EXE: "+hex(WORDd['Addr'])+" "+str(bytes(args)).replace("b'","'",1)+" {f.yellow}(END_PARAM){r}")
                try:
                    if retbytes == True:
                        bytelines.append( bytes([WORDd["Addr"],*args]) )
                    else:
                        exec_line( bytes([WORDd["Addr"],*args]) )

                except Exception as e:
                    fprint("{f.red}ERROR: "+e+"{r}")
                # reset
                traversed = 0
                WORDd = None
                args = []
                found_dyn_param_len_byte = 0
    if retbytes == True:
        return bytelines

# MARK: Interpriter
from _lib_fuse_legacy_ui import Text,Console

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument("-path","-p",dest="path")
parser.add_argument("--d",dest="debug",action="store_true")
parser.add_argument("--e",dest="autoexit",action="store_true")
parser.add_argument("--no-warn",dest="no_warn",action="store_true")

parser.add_argument("-rich-usage-mode",dest="format_rich_usage_mode")
parser.add_argument("-color-system",dest="format_color_system",help='"auto" / "standard" / "256" / "truecolor" / "windows"')
parser.add_argument("--win-try-enable-ansicol",dest="format_win_try_enable_ansicol",action="store_true")
parser.add_argument("--no-color",dest="format_no_color",action="store_true")

parser.add_argument("-conv-byte",dest="conv_byte_path")
parser.add_argument("-conv-byte-conf",dest="conv_byte_conf")

parser.add_argument("-conv-text",dest="conv_text_path")
parser.add_argument("-conv-text-sep",dest="conv_text_sep",help="COMMA / SPACE (def)")
parser.add_argument("-conv-text-bnom",dest="conv_text_bnom",help="ByteNormalization: 'auto' / <len> (-1 to disable)")
parser.add_argument("-conv-text-cmtmode",dest="conv_text_cmts",help="DEVDOC / EMPTY (if not given, no comments)")
parser.add_argument("--conv-text-addr-methods",dest="conv_text_addrs",action="store_true")
parser.add_argument("--write-example",dest="write_example",action="store_true")

pargs = parser.parse_args()


# Setup text
con = Console(
    useRich = pargs.format_rich_usage_mode if pargs.format_rich_usage_mode != None else "auto",
    winTryEnaAnsiCol = pargs.format_win_try_enable_ansicol,
    color_system = pargs.format_color_system if pargs.format_color_system != None else "auto",
    no_color = pargs.format_no_color,

)
text = Text(terminal=con.terminal)
def fprint(t,*args,**kwargs):
    print(text.parse(t),*args,**kwargs)

# Warn
if pargs.no_warn != True:
    fprint("{f.yellow}DUMB-lang is in very early development and methods and their adresses probably will change or be removed!\n(To disable this warning start with the {italic}--no-warn{no_italic_no_bl}){r}")

# MARK: ExampleProgram
if pargs.write_example == True:
    fprint("{f.magenta}{italic}[ Wrote examples to *intep*/examples ]{r}")
    HEAD1  = [0b0_000_0010]
    HEAD2  = [0b0_000_0001]
    HEAD3  = [0b0_000_0000]
    REGIp = []
    BLOBp = []
    EXEC1  = [
        0x02,0xFF,       # LOCK 255
        0x03,0x00,       # FILL NULL

        0x3A,            # WPOK (Walk-POKE)
        0x0C,          # ParamLength: 12 (Since WPOK is a dynamic_param_lenght method)
        0x00,          # Start STACKPOS
        # Hello world!
        0x48,0x65,0x6C,0x6C,0x6F, 0x20, 0x77,0x6F,0x72,0x6C,0x64,0x21,
        0x0B,0x00,0x0B,  # WALK 0x01 to 0x0B
        0x12,            # PRES
    ]
    EXEC2 = [
        0x02,0xFF, # LOCK 255
        0x03,0x00, # FILL NULL

        0x08,0x00,0x48, # POKE H
        0x08,0x01,0x65, # POKE e
        0x08,0x02,0x6C, # POKE l
        0x08,0x03,0x6C, # POKE l
        0x08,0x04,0x6F, # POKE o
        0x08,0x05,0x20, # POKE " "
        0x08,0x06,0x77, # POKE w
        0x08,0x07,0x6F, # POKE o
        0x08,0x08,0x72, # POKE r
        0x08,0x09,0x6C, # POKE l
        0x08,0x0A,0x64, # POKE d
        0x08,0x0B,0x21, # POKE !
        0x0B,0x00,0x0B, # WALK 0 - 11
        0x12,           # PRES
    ]
    parent = os.path.dirname(os.path.abspath(__file__))
    open(os.path.join(parent,"examples","helloworld_short.dumb"),'wb').write(combine_byte_file(HEAD1,EXEC1,BLOBp,REGIp))
    open(os.path.join(parent,"examples","helloworld.dumb"),'wb').write(combine_byte_file(HEAD1,EXEC2,BLOBp,REGIp))
    open(os.path.join(parent,"examples","helloworld_content.dumb"),'wb').write(combine_byte_file(HEAD2,EXEC2,BLOBp,REGIp))
    open(os.path.join(parent,"examples","helloworld_full.dumb"),'wb').write(combine_byte_file(HEAD3,EXEC2,BLOBp,REGIp))


INTEP_INTERACTIVE = False
if pargs.path == None:
    INTEP_INTERACTIVE = True
else:
    pargs.path = os.path.abspath(pargs.path)

INTEP_RUNNING = True

FOUND_VEND_ADDR = None
for x in REGI.getDecl(BLOBSTORE):
    if x["Name"] in ["VEND","VEND".encode(ENCODING)]:
        FOUND_VEND_ADDR = x["Addr"]
        break

def intep_debug_print(*args,**kwargs):
    if pargs.debug == True:
        fprint(*args,**kwargs)


try:
    if INTEP_INTERACTIVE == True:
        ENVIR_HEADER = "PROMPT"
        BLOBSTORE = REGI.ensure_blobstore_adresses(BLOBSTORE)
        lcu.setConTitle(f"DUMB {FRIENDLY_VERSION} ^| Interactive Prompt")
        while INTEP_RUNNING == True:
            try:
                inp = input("> ")
                if inp.strip() != "":
                    exec_cli_input(inp,False)
            except Exception as e:
                fprint("{f.red}ERROR: "+e+"{r}")
    else:
        if INTEP_RUNNING == True and os.path.exists(pargs.path):
            cli_content = None
            try:
                with open(pargs.path,'r',encoding=ENCODING) as f:
                    content = f.read()
                    if content.lstrip().lstrip("\n").lstrip().startswith(".source"):
                        cli_content = content.replace(".source","",1)
            except: pass
            if cli_content != None:
                BLOBSTORE = REGI.ensure_blobstore_adresses(BLOBSTORE)
                lcu.setConTitle(f"DUMB {FRIENDLY_VERSION} ^| Executing {os.path.basename(pargs.path)}... (Mode:TEXT)")
                ENVIR_HEADER = "SOURCE_FILE"
                BLOBSTORE = REGI.set_blobstore_entry(BLOBSTORE,0x03, bytes([
                    0b00_000000, *strToBytes(os.path.dirname(pargs.path))
                ]))
                bytelines = []
                for line in cli_content.split("\n"):
                    if line.strip() != "":
                        try:
                            if pargs.conv_byte_path != None:
                                bytelines.append(
                                    exec_cli_input(line,True)
                                )
                            else:
                                exec_cli_input(line,False)
                        except Exception as e:
                            fprint("{f.red}ERROR: "+e+"{r}")
                # TEXT -> BYTE
                if pargs.conv_byte_path != None:
                    VERS = format(COMP_FILEVER,'03b') # XXX
                    CONF =                     '0010' # XXXX
                    if pargs.conv_byte_conf != None:
                        CONF = pargs.conv_byte_conf
                    HEAD = binToByte(f"0{VERS}{CONF}")
                    EXEC = bytes()
                    for line in bytelines:
                        EXEC = EXEC + line
                    open(pargs.conv_byte_path,'wb').write(
                        combine_byte_file([HEAD],EXEC,[],[])
                    )
            else:
                TYPE,VERS,CONF,EXEC,BLOB = readDumbFile(pargs.path)
                ENVIR_HEADER = f"T={TYPE};V={format(VERS,'03b')};C={format(CONF,'04b')}"
                conf = byteToBinStr(CONF)[-4:]
                # config "0001" has no regi included, include iterpriters to newly-read BLOBSTORE instance
                #   also update paths
                if conf.endswith("01"):
                    # Update regi
                    BLOB = REGI.set_blobstore_entry(BLOB,0x00, REGI.get_blobstore_entry(BLOBSTORE,0x00) )
                    # Update 0x02,0x04,0x05 (not 0x03 since it's set bellow)
                    BLOB = REGI.set_blobstore_entry(BLOB,0x02, REGI.get_blobstore_entry(BLOBSTORE,0x02) )
                    BLOB = REGI.set_blobstore_entry(BLOB,0x04, REGI.get_blobstore_entry(BLOBSTORE,0x04) )
                    BLOB = REGI.set_blobstore_entry(BLOB,0x05, REGI.get_blobstore_entry(BLOBSTORE,0x05) )

                # config 0010 has no BLOBSTORE at al, include interpriters to newly-read BLOBSTORE instance
                elif conf.endswith("10"):
                    BLOB = BLOBSTORE
                
                # Continue
                lcu.setConTitle(f"DUMB {FRIENDLY_VERSION} ^| Executing {os.path.basename(pargs.path)}... (Mode:BYTE)")
                BLOBSTORE = REGI.ensure_blobstore_adresses(BLOB)
                BLOBSTORE = REGI.set_blobstore_entry(BLOBSTORE,0x03, bytes([
                    0b00_000000, *strToBytes(os.path.dirname(pargs.path))
                ]))
                bytelines = []
                
                if pargs.conv_text_path != None:
                    bytelines = exec_byte_inp(EXEC,True)
                else:
                    exec_byte_inp(EXEC,False)

                # BYTE -> TEXT, CMNT?
                if pargs.conv_text_path != None:
                    lines = [".source"]
                    found_lock_arg = None
                    for byteline in bytelines:
                        # split
                        WORD = byteline[0]
                        args = []
                        if len(byteline) > 1:
                            for byte in byteline[1:]:
                                args.append(byte)
                        # handle WORD
                        WORDb = formatToHexlen(WORD,2)
                        if pargs.conv_text_addrs == True:
                            WORD = WORDb
                        else:
                            WORDn = REGI.getDecl_bname(BLOBSTORE,WORD).get("Name",None)
                            WORD = WORDn.decode(ENCODING) if WORDn != None else WORDb
                        # handle args
                        if pargs.conv_text_bnom == None: pargs.conv_text_bnom = "auto"
                        if pargs.conv_text_bnom.lower() == "auto":
                            # ensure lock arg
                            if found_lock_arg == None:
                                big = -1000
                                for byteline2 in bytelines:
                                    if byteline2[0] == 0x01: # LOCK
                                        if byteline2[1] > big:
                                            big = byteline2[1]
                                if big > -1000:
                                    found_lock_arg = big
                            # auto normalize argument bytes
                            nargs = []
                            for byte in args:
                                if found_lock_arg == None:
                                    nargs.append( formatToHexlen(byte, 2 ) )
                                else:
                                    n = found_lock_arg
                                    if n == 0: n = 1
                                    else: n = len(hex(n)[2:])
                                    nargs.append( formatToHexlen(byte, n ) )
                        else:
                            nargs = []
                            for byte in args:
                                nargs.append( formatToHexlen(byte, int(pargs.conv_text_bnom) ) )
                        if pargs.conv_text_sep != None:
                            sep = pargs.conv_text_sep
                        else:
                            sep = " "
                        # build strings
                        if len(nargs) > 0:
                            nsargs = " "+sep.join(nargs)
                        else:
                            nsargs = ""
                        line = WORD+nsargs
                        lines.append(line)
                    
                    if pargs.conv_text_cmts == None:
                        nlines = lines
                    else:

                        # find longest .rstrip():ed line
                        longest = 0
                        for line in lines:
                            if not line.lstrip().startswith("."):
                                l = len(line.rstrip())
                                if l > longest: longest = l
                        
                        # Apply comments?
                        nlines = []
                        for line in lines:
                            if not line.lstrip().startswith("."):
                                ex = longest - len(line.rstrip())
                                # apply DEVDOC
                                if pargs.conv_text_cmts.lower() == "devdoc":
                                    b = REGI.getDecl_bname(BLOBSTORE,line[:4])
                                    if b != None:
                                        b = b.get("Name",None)
                                    if b != None:
                                        b = METHOD_NAME_TO_DESC.get(b,None)
                                # Just comments
                                else:
                                    b = None
                                if b == None: 
                                    b = ""
                                line = line + " "*ex + " # " + b
                                nlines.append(line)
                            else:
                                nlines.append(line)

                    if len(nlines) > 0:
                        with open(pargs.conv_text_path,'w',encoding=ENCODING) as f:
                            f.write( '\n'.join(nlines) )
                            f.close()
                    

except KeyboardInterrupt:
    print("POKE Px00 0x42\n> POKE Px01 0x79\n> POKE Px02 0x61\n> POKE Px03 0x61\n> POKE Px04 0x21\n> WALK Px00,Px04\n> PRES\nByaa!")
