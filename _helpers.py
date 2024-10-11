def intToHexByte(num):
    if 0 <= num <= 255:  # Ensure the number is within byte range
        # Convert to byte and format as hexadecimal string
        hex_string = f"0x{num:02X}"
        return hex_string
    else:
        raise ValueError("Input must be between 0 and 255.")

def intToBinaryStr(num, bits=8):
    if num < 0:
        raise ValueError("Input must be a non-negative integer.")
    # Convert to binary and strip the '0b' prefix
    binary_string = bin(num)[2:]  
    # Pad with leading zeros to ensure the length is equal to 'bits'
    padded_binary_string = binary_string.zfill(bits)
    return padded_binary_string

def strToBytes(s):
    # Convert each character to its ASCII value
    hex_bytes_list = [ord(char) for char in s]
    return hex_bytes_list

def starts_with(list1, list2):
    # Check if list1 starts with the elements of list2
    return list1[:len(list2)] == list2

def binToByte(binary_str):
    # Ensure the input is a valid 8-bit binary string
    if len(binary_str) != 8 or not all(bit in '01' for bit in binary_str):
        raise ValueError("Input must be an 8-bit binary string.")
    
    # Convert the binary string to an integer
    return int(binary_str, 2)

def split_bytes_by_delimiter(data: bytes, delimiter: int = 0x17) -> list:
    ndata = []
    if delimiter in data:
        ndata = data.split(bytes([delimiter]))
    return ndata

def byteToBinStr(byte):
    return format(byte, '08b')
    
def formatToHexlen(x,length=2):
    if length < 0: return f"{hex(x)}"
    if length < 10:
        lengths = f"0{length}"
    else:
        lengths = str(length)
    return f"0x{format(x,f"{lengths}x")}"

def shiftList(lst, x):
    # Shift the list by x positions
    x = x % len(lst)  # To ensure x is within the list's bounds
    return lst[-x:] + lst[:-x]

def unshiftList(lst, x):
    # Shift the list backward by x positions
    x = x % len(lst)  # To ensure x is within the list's bounds
    return lst[x:] + lst[:x]

def shiftListNonOverlap(lst, x, fill_value):
    # Shift the list by x positions without overlap
    x = x % len(lst)  # To ensure x is within bounds if larger than list length
    return [fill_value] * x + lst[:-x]

def unshiftListNonOverlap(lst, x, fill_value):
    # Unshift the list by x positions and fill the end with fill_value
    x = x % len(lst)  # To ensure x is within bounds if larger than list length
    return lst[x:] + [fill_value] * x

def splitBytesInFourChunks(input_bytes: bytes):
    chunk_size = 4
    # Split the bytes into chunks of 4
    chunks = [input_bytes[i:i + chunk_size] for i in range(0, len(input_bytes), chunk_size)]
    # Check if there is a remainder
    remainder = b''
    if len(input_bytes) % chunk_size != 0:
        remainder = chunks.pop()
    return chunks, remainder