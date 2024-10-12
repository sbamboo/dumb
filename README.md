# DUMB Lang
*Made by: Simon Kalmi Claesson*

## Disclamer!

- **This is a joke programming language and not meant for actuall projects.**

- **The project is also in very early development, and methods and their adresses probably will change or be removed!**

## The idea
DUMB is a psudo-stack based language, and uses a **Stack** for saving data, aswell as a content-holder for binary data called **BlobStore** and a result-buffer called **Result**.

Values, indexes and adresses are written with prefixed-hex codes example `0xFF` for `255`.

The language has different methods for operations, that can either be called by an al-capsed four letter name, example `LOCK` or their method-adress, example `0x02`.

The stack is a fixed length list of binary-objects, that can be locked to a specified **STACKLEN**.

The result-buffer is a binary object where if a list is written too it, it will contain multiple bytes, this allows you to store a tex. *text* and *numbers*. Otherwise it will be just one byte long.

The BlobStore can be used to include larger content into the code, for example filepaths and functions. (So called "voids")

## Setup Enviroment / Project
1. Install the python-dependencies:
  Run `pip install -r requirements.txt` using the *requirements* file.
2. Generating examples: 
  1. Run `python intep.py --write-example` **(Make sure you are running the folder of intep.py!)**
  2. Check the "examples" folder.
3. Running the *prompt*/*interactive-interpriter*:
  1. Run `python intep.py`


## Version 0.0

### Methods
To get a list of al methods and their adresses one can use the `INFO` method.

Al methods are declared with a *input_type* as one of:
- `NONE`: No arguments.
- `ONLY`: Only the specified strict-parameters.
- `RNGE`: Includes parameters that should be recognized as start and end of a range.
- `FROM`: Specifies the parameters should include either `*` or `POS*` in the declaration aswell as the method taking dynamic-parameters. *(See Interpriter-Features)*

Al methods are also declared with a list of *parameter_types*, one for each parameter the argument takes. (Or *\** / *POS\** for dynamic-parameters.)
The types should be declared with one of:
- `UNKNOWN`
- `HEXx`: A HEX-value with the length least-needed to adress the *stack*. *(For a `256` entries long stack that would be two symbols.)*
- `HEX`: Any length of HEX-value.
- `HEX1`, `HEX2`, `HEX4`, `HEX6`, `HEX8`: HEX-value with specific length.
- `CHAR`: Text-value denoting a text character.
- `HEXCHAR`: HEX-value denoting a text character.
- `NUMBER`: Text-value denoting a number character.
- `HEXNUMBER`: HEX-value denoting a number character.
- `BLOBINDEX`: A HEX-value for a *BlobStore* adress.
- `PATHINDEX`: A HEX-value for a *BlobStore* adress where a filepath is stored.
- `*`: Dynamic parameter method, where the length is given as value for the first argument.
- `POS*`: Dynamic parameter method, where the length is stored in the *stack* and the first argument is the position to where in the *stack* the lenght is stored.

**(The *parameter_type* is used mostly as contextual information)**

### Result
You can print the result-buffers content using the `PRES` method, but it always interprites the bytes as ASCII meaning if you write a number like `0x00` (`0`) it will be shown as a NULL character. To convert the bytes to their number character you can use the `TINT` method *(to-int)* or `FINT` *(from-int)* to get it back.

### BlobStore
Some blobstore entries are filled in by the interpriter and are not *usually* adressable by the user:
- `BlobStore.0` is *usually* the internal method registry.
- `BlobStore.1` is *usually* holding the result-buffer.
- `BlobStore.2` is *usually* the parent-path to the interpriter.
- `BlobStore.3` is *usually* the parent-path to the file (or the interpriter if run in a prompt)
- `BlobStore.4` is *usually* a preset filename.
- `BlobStore.5` is *usually* a preset filename.

The blobstore entries are sepparated by a `0x07` byte followed by one config-byte for telling what the entry is.
The first two bits in the config-byte tells its type:
- `00`: A filepath.
- `01`: A function. ("void")
- `10`: A method registry.
- `11`: A result blob.

The following six bits are configuration *flags*/*modes* for the blob, example how it should be read.

**NOTE! Since the `0x07` byte is used a sepparator no data in the *BlobStore* can contain the byte, this means 0x17 is not a valid command-adress, and *Voids* will be stored encoded in *Base64*.**

This means the blobstore adressables are usualy anything higher then *0x05*
The blobstore is always `256` entries long.

### Stack
The stack can be exported to a filepath stored in the *BlobStore* using the `EXPR` method and imported back using the `FAKE` method.

### Registry
The registry contains the declaration information for commands, excluding eventual *DEVDOC-Descriptions*.

Since the registry is stored in *BlobStore* it is al in byteform.
Al entries follows the format `DDDDDDDD NNNNNNNN NNNNNNNN NNNNNNNN NNNNNNNN TTTTLLLL XXXXXXXX...`.
- `D-byte`: Stores the declaration-adress for the method.
- `N-byte`: Each character of the name for the method, *(Thus four N-byte:s)*
- `TL-byte`: Contains four-bits for *input_type* and then four-bits for *parameter_length*.<br>
For dynamic-length methods, the *parameter_length* does not include the *dynamic-length-argument* but includes the *dynamic-type-argument* (`*` or `POS*`).
- `X-byte`: Stores the *parameter_type* *(Thus one X-byte for parameter length)*

The binary *parameter_type*s are:
- `00000000`: UNKNOWN
- `00000001`: HEXx *(by len-of-operations)*
- `00000010`: HEX
- `00000011`: HEX1
- `00000100`: HEX2
- `00000101`: HEX4
- `00000111`: HEX6
- `00001000`: HEX8
- `00001001`: CHAR
- `00001010`: HEXCHAR
- `00001011`: HEXNUMBER
- `00001100`: NUMBER
- `00001101`: BLOBINDEX
- `00001111`: PATHINDEX
- `00010000`: \*    *(Used when type is FROM)*
- `00010001`: POS\* *(Used when type is FROM, and LEN comes from a POS)*


### File formats
Dumb lang uses the `.dumb` file-type.
It can be used in thre scenarios:
- `TEXT_CODE`
- `BINARY_CODE`
- `STACK_EXPORT`

When used for `TEXT_CODE` the file stores the same input as you would put into the *prompt*/*interactive-terminal*.
This means it can also include comments.
It is praxis to put al comments aligned to the right:
```dumb
LOCK 0xFF                # Comment
FILL 0x00                # Comment
WPOK 0x02 0x00 0xFE 0xFF # Comment
```

When used for `BINARY_CODE` or `STACK_EXPORT` the file stores only binary data.
The first byte is the *config-byte*, otherwise known as `HEAD`.
The *config-byte* is always in the format of `TVVVCCCC`:
- `T-bit`: Denotes the use of the binary file. (`0` for `BINARY_CODE` and `1` for `STACK_EXPORT`)
- `V-bit`: The three *V-bit:s* denotes the compatible *Dumb-Lang Binary-File-Format* version.
- `C-bit`: The four *C-bit:s* denote config flags/modes for the file.
  - `0000`: The file contains both Code *(`EXEC`)* and the full *BlobStore*, including both the method-registry *(`REGI`)* and the other blobstore content *(`BLOB`)*.
  - `0010`: The file contains the Code *(`EXEC`)* and some *BlobStore* content, mainly excluding the method-registry and having just the other content *(`BLOB`)*.
  - `0011`: The file conttains just the Code *(`EXEC`)*.

As previously noted the *BlobStore* is sepparated via `0x17` bytes, the same applies here. This means when disecting a *.dumb* binary file in `BINARY_CODE` mode, one can easily see where the *BlobStore* entry begins when the first `0x17` byte is found.

When the file is used for `STACK_EXPORT` al bytes after the *config-byte* are *stack-byte*:s and can include for-example `0x17` if that is the value of the stack.

### Interpriter Features
- **Dynamic-ParameterLength-Methods**<br>
  Methods with the `FROM` *input_type* and that use either `*` or `POS*` as a *parameter_type* are handled parsed with a dynamic length of parameters. This is neccessairy since *binary-mode* code file have a strict parameter count for each method. These methods always take the *amount* of dynamic-parameters as a value for the first argument, followed by strict-parameters and then the specified amount of dynamic ones.

  An example would be `WPOK` which *Walk-Pokes* multiple values into the *stack*. To poke two values starting from position `0x00` we can use `WPOK 0x02 0x00 0xFE 0xFF`, where the first argument `0x02` is the amount of dynamic parameters and the second `0x00` is a strict-parameter for starting-stack-position, followed by `0xFE` and `0xFF` as dynamic-parameters.

### DEVDOC (Method list, W.I.P)
#### Examples
`LOCK 0xFF`<br>
Sets the default stack to on-init be FF/255 slots long, this locks the program to this len-of-operations

`FILL 0x00`<br>
Fills the stack with 0x00/ASCII.null
<br><br>

`FAKE Sx00`<br>
Reads the blob at INDEX.0 as a PATH and loads it as stack.

`EXPR Sx00`<br>
Reads the blob at INDEX.0 as a PATH and writes the current stack to it.

`BACK`<br>
Returns to the default stack

`INFO`<br>
Makes the interpriter print out info about DUMB.

`POKE Px01,0x00`<br>
Opens the stack at position Px00/INDEX.0 and puts 0x00/ASCII.null

`WACK Px01`<br>
Clears position Px01/INDEX.1 of the stack.

`SWAP Px00,Px01`<br>
Swaps the contents of the stack at INDEX.0 and INDEX.1
<br><br>

`WALK Px00,Px06`<br>
Returns the content of the stack between INDEX.0 and INDEX.6 to RESULT.

`PEEK Px01`<br>
Gets the content of the stack at pos 0x01/INDEX.1 to RESULT.

`MAXL`<br>
Returns the max-lenght of the current STACK to RESULT.

`GRES Px00,Px06`<br>
Puts al the content from RESULT into the current stack until end, or if end is same as front truncated till stack-end.
<br><br>

`DICE 0x01,0x06`<br>
Returns a random entry from the range 0x00 to 0x06 (INCLUSIVE) to RESULT.

`TAKE`<br>
Asks the interpriter for text input and sends to RESULT.
<br><br>

`CRES`<br>
Clears the RESULT.

`PRES`<br>
Prints the content of RESULT converted to ASCII to the interpriter.

`LRES Px00`<br>
Returns the length of the RESULT to Px00/INDEX.0 in stack.
<br><br>

`YEET`<br>
Exits the program.

`WAIT 0x000000`<br>
Waits for hex->int ms.
<br><br>

`VOID`<br>
Starts saving lines until VEND.

`VEND Ix01`<br>
Saves lines from last VOID into Ix00 BLOB-INDEX.0

`CALL Ix01`<br>
Calls lines stored in BLOB-INDEX.0
<br><br>

`JPAT Sx01,Sx02,Sx03`<br>
Joins the paths in 01 and 02 to 03.
<br><br>

`HACK`<br>
Converts the RESULT to ASCII and tells the interpriter to run it in as a system command.
<br><br>

`ADDT 0x00,0x00`<br>
Adds two numbers (0+0) and puts to RESULT.

`SUBT 0x00,0x01`<br>
Subtracts 0 from 1 and puts to RESULT.

`MULT 0x00,0x00`<br>
Multiplicates two numbers (0,0) and puts to RESULT.

`DIVT 0x10,0x02`<br>
Divides 10 by 2 and puts the positive rounded result to RESULT.

`FLDT 0x10,0x02`<br>
Floor divides 10 by 2 and puts to RESULT.

`POWT 0x02,0x02`<br>
Calculates 2^2 and puts to RESULT.

`MODT 0x11,0x02`<br>
Floor divides 11 by 2 and puts to RESULT.
<br><br>

`ADDS Px00,Px00`<br>
Same as ADDT but from STACK to RESULT.

`SUBS Px00,Px00`<br>
Same as SUBT but from STACK to RESULT.

`MULS Px00,Px00`<br>
Same as MULT but from STACK to RESULT.

`DIVS Px00,Px00`<br>
Same as DIVT but from STACK to RESULT.

`FLDS Px00,Px00`<br>
Same as FLDT but from STACK to RESULT.

`POWS Px00,Px00`<br>
Same as POWT but from STACK to RESULT.

`MODS Px00,Px00`<br>
Same as FDVT but frmo STACK to RESULT.
<br><br>

`TINT`<br>
Converts the content of RESULT to the eqvivelent number char and returns to RESULT.

`FINT`<br>
Converts a character byte to numeralbyte. (Content of RESULT to equiv hexnum and returns to RESULT)

`TBOl`<br>
Interprites the RESULT to BOOL placed to RESULT.

`FBOl`<br>
Interprites the RESULT from BOOL placed to RESULT.
<br><br>

`REVS`<br>
Reverses the stack.
<br><br>

`IFIS Ix00,Px00,Px01`<br>
CALLS void at Ix00 if value at stack Px00 is value at stack Px01.

`IFNO Ix00,Px00`<br>
CALLS void at Ix00 if value at stack Px00 is NOT value at stack Px01.

`IFGT Ix00,Px00,Px01`<br>
CALLS void at Ix00 if STACK.0 > STACK.1

`IFLT Ix00,Px00,Px01`<br>
CALLS void at Ix00 if STACK.0 < STACK.1
<br><br>

`FORP Ix00,Px00`<br>
CALLS void at Ix00 STACK.0 times.

`FORR Ix00`<br>
CALLS void at Ix00 RESULT times.

`FORE Ix00`<br>
For each entry in result (multiple post-walk) call VOID.
<br><br>

`WHIL Ix00,Px00,Px01`
CALLS void at Ix00 while value at stack Px00 is value at stack Px01.

`WHIR Ix00,Px00`<br>
CALLS void at Ix00 while RESULT is value at stack Px00.
<br><br>

`BRCK`<br>
Breaks an interation.

`GETI`<br>
Gets the current interation index and put to RESULT.
<br><br>

`WPOK 0x02,Px00,0x67,0x67`<br>
Walk-Pokes "gg" to the STACK starting at pos Px00.
DYN_PARAM_LEN_METHOD:
  Thus the first argument must be the amount of additional arguments, the command takes in this call. (in this case 2 for the last two args since the first two are required)

`WPKR Px00,Px01,0x67,0x67``<br>
Walk-Pokes "gg" to the STACK starting at pos Px01.
DYN_PARAM_LEN_METHOD:
  Thus the first argument must be the amount of additional arguments, WPKR differs from WPOK in that the arg-len is read from POS. (in this case Px00)
  Here there should be 0x02 in Px00 for the two last args.
<br><br>

`SWPB Ix00,Ix01`<br>
Swaps the content in two BLOBSTORE adresses.
<br><br>

`SHFT 0x01`<br>
Shifts the stack forwards by 0x01. (Overlapping)

`USHT 0x01`<br>
Shifts the stack backwards by 0x01. (Overlapping)

`SFTN 0x01`<br>
Shifts the stack forwards by 0x01. (Truncating)

`UFTN 0x01`<br>
Shifts the stack backwards by 0x01. (Truncating)
<br><br>

`EXIS Px00,Sx06`<br>
Checks if the file from Sx06 exists and returns 0 or 1 to pos.0

`EXIR Sx06`<br>Checks if the file from Sx06 exists and returns 0 or 1 to RESULT.

`REMA Sx06`<br>
Removes the filepath in Sx06. (asks if exists)

`REMF Sx06`<br>
Removes the filepath in Sx06. (forced)

`WRTE Sx06`<br>
Writes the stack to the file in Sx06 as raw bytes.

`WRTS Sx06 0x00 0x01`<br>
Writes the stack from index 0x00 to index 0x01 to the file in Sx06 as raw bytes.

`WRTR Sx06`<br>
Writes the RESULT to the file in Sx06 as raw bytes.

`READ Ix07,Sx06`<br>
Reads the content of the file in Sx06 as raw bytes to Ix07.

`REDR Sx06`<br>
Reads the content of the file in Sx06 as raw bytes to RESULT.

`APEW Sx06`<br>
Appends the STACK to the file in Sx06. (as bytes)

`APES Sx06 0x00 0x01`<br>
Appends the STACK from index 0x00 to index 0x01 to the file in Sx06. (as bytes)

`APER Sx06`<br>
Appends the RESULT to the file in Sx06. (as bytes)
<br><br>

`EVAL`<br>
Evaluates the RESULT as binary-source.

`ARGS`<br>
Puts any CLI params into RESULT as a list.
<br><br>

`REPL 0x01 0x02`<br>
Replaces each entry of 0x01 in the STACK with 0x02.

`REPR 0x01 0x02`<br>
Replaces each entry of 0x01 in RESULT.with 0x02.

`DELE 0x01`<br>
Empties each instance of 0x01 in the STACK.

`DELR 0x01`<br>
Empties each instance of 0x01 in RESULT.
 
`FIND 0x01`<br>
Returns al the indexes where 0x01 is in the STACK to RESULT as a list.

`FINO 0x01`<br>
Finds the first index where 0x01 is found in the STACK, and returns to RESULT.
<br><br>

`SPLT 0x01`<br>
Split the stack at each entry of 0x01, and return as list to RESULT.

`SPLB 0x01`<br>
Split the stack at the first entry of 0x01 and return the before-content to RESULT.

`SPLA 0x01`<br>
Split the stack at the first entry of 0x01 and return the after-content to RESULT.

## TODO
- ☑ Add advanced formatting support to interpriter.
- ☐ Implement `ARGS`, `SPLT`, `SPLB` and `SPLA`.
- ☐ Move commands into a CONF-flag for the `Extended-Method Set`.
- ☐ Reorder commands. **(Will change adresses!)**
- ☐ Graphics Mode with: (Under `Graphics-Method Set`)
  `GBI1 <width> <height>` (GraphicsBufferInit_Mode1)
    Adds W*H adresses to the stack, disables LOCK until `GBPU`.
    Adresses are mapped to x,y in a zig-zag pattern.
    Mode1: "Palette" 1byte/cell, allows text, only paletted colors 
  `GBI2 <width> <height>` (GraphicsBufferInit_Mode2)
    Adds W*H adresses to the stack, disables LOCK until `GBPU`.
    Adresses are mapped to x,y in a zig-zag pattern.
    Mode1: "8bit" 1byte/cell, only colors no text, but uses al 256 8bit colors.
  `GBCL` (GraphicsBufferClear)
    Clears the added adresses.
  `GBPK <x> <y> <val>` (GraphicsBufferPoke)
    Pokes an adress based on its equivelent x,y position.
  `GBPE <x> <y>` (GraphicsBufferPeek)
    Gets the content at an adress based on its equivelent x,y position.
  `GPSM <drawModeIndex>` (GraphicsBufferSetDrawMode)
    Modes are:
    - `0x00`: Char / HalfWidth (Char is drawn as normal)
    - `0x01`: Double (Text is drawn on everyother cell)
    - `0x02`: HighRes (Text is drawn if same char under itself at same y)
  `GBDR` (GraphicsBufferDraw)
    Draws the buffer.
  `GBPU` (GameBufferPurge)
    Purges the buffer.