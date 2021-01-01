# In-memory format

These arrays store mob data. Each holds 2 bytes per mob. 

* `$7e8000`
    * first byte is sprite ID
    * second byte initialized to zero
* `$7e8200`
    * second byte is animation state (whether moving, direction, animation frame)
* `$7e8400`
* `$7e8600`
* `$7e8800`
* `$7e8a00`
* `$7e8c00`
* `$7e8e00` X coordinate
* `$7e9000` Y coordinate
* `$7e9200` Strangely packed version of coordinates, only for visible mobs
* `$7e9400` AI data? Always `00 00` for party members, but only when in your party
* `$7e9600` Initial X coordinate
* `$7e9800` Initial Y coordinate
* `$7e9a00`
* `$7e9c00`
* `$7e9e00` ?? Has the following values. Non-zero values are unique and used in ascending order:
    * `0x01-0x0d` for various NPCs, most seem to be (potential) party members
    * `0x00` for all other NPCs and spawned mobs
    * `0x0e` for empty slot 171 
    * `0x0f` for empty slot 174 
    * The memory immediately after, `$7ea000`, has a compacted version of this array using only 1 byte per mob

# Mob IDs

* Indexes 0-167 (i.e. offsets $0000 to $014f) are reserved for NPCs, who always seem to appear in the same order
* Indexes 168-203 (i.e. offsets $0150 to $0197) seem to usually be empty
* Indexes 203-255 (i.e. offsets $0198 to $01ff) seem to be room for spawned mobs

The values at `$a7` and `$a9` seem to indicate the range of NPCs are active in the current region:
* `0x04`-`0x50` in the overworld/indoors
* `0x50`-`0x52` in the castle & buc's den catacombs

# Mob loading
   
These fields are loaded in a function at `$181b4` during boot:

* `$7e8000`
    * First byte (sprite ID) is loaded from ROM address `f058`, 1 byte per mob 
    * Second byte is initialized to 0
* `$7e8200`
    * First byte is initialized to 0
    * Second byte is loaded from ROM address `eb34`, 1 byte per mob, then binary-ANDed with `0x0f`
* `$7e8400`
    * First byte is loaded from ROM address `ebf0`, 1 byte per mob
    * Second byte is loaded from ROM address `ecac`, 1 byte per mob
* `$7e8600`
    * First byte is loaded from ROM address `ed68`, 1 byte per mob
    * Second byte is loaded from ROM address `ef9c`, 1 byte per mob
* `$7e8800`
    * Loaded from ROM address `ee24`, 2 bytes per mob
* `$7e9c00`
    * Initialized to 0

The function at `$388af` loads more during boot, though I haven't read through it fully so this may be inaccurate:

* `$7e8200`, `$7e8e00` & `$7e9000` (X & Y coordinates), `$7e9600` & `$7e9800` (initial X & Y coordinates?)
    * Loaded from ROM address `18c3d`, 4 bytes per mob
    * X coordinate gets the first 10 bytes
    * Y coordinate gets next 10 bytes
    * `$7e8200` first byte gets the 3rd byte from ROM

# Sprite loading

Palette index (0-7) comes from `f159` on ROM + sprite ID. However, some sprite render functions use hard-coded 
palettes and ignore this value.  

Sprite data is loaded in "rows", which are each `0x400` bytes of tile data (32 8x8 tiles) stored in 
[SNES graphics format](https://www.raphnet.net/divers/retro_challenge_2019_03/qsnesdoc.html#GraphicsFormat).

Each sprite ID is mapped to a row ID, then the row ID is used to look up the address of the sprite data.

## Row mapping table 

There's a lookup-table mapping each sprite ID to one or more row IDs of graphics data 
at `$02e735` in memory / `16735` on ROM (1 byte per sprite):
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
0   01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f 10
10  15 00 14 13 15 28 16 17 18 19 1a 19 1b 14 1d 18
20  1e 15 1b 1e 14 a0 21 17 1c 22 23 1d 24 25 26 33
30  67 28 29 6a 6b ac 2d 2e 29 16 2f 30 30 30 30 30
40  1a 1c 13 11 31 31 01 12 12 01 32 13 13 33 30 30
```

Each byte is `nniiiiii`

* `nn` represents how many rows of sprite data are needed for the sprite
    * `00` - 1 row.
    * `01` - 2 rows.
    * `10` or `11` - 4 rows.
* `iiiiii` represents the index into the row address table of the first row. Subsequent rows are found by incrementing
    the address by `0x400`

## Row address table

At `$02e79b` in memory / `1679b` in ROM there is a table of addresses for each row ID (3 bytes per row ID):
```
00  00302a 00e41d 00900f 00940f 00980f 009c0f 00a00f 00a40f
08  00a80f 00ac0f 00b00f 00b40f 00b80f 00bc0f 00c00f 00c40f
10  00c80f 00e01f 00ec0f 00841f 00e40f 00ac1f 00a81f 00d80f
18  00f00f 00dc0f 009c1f 00f40f 00ec0f 00a41f 00a01f 008c1f
20  00c01f 00d01f 00f80f 00e80f 00d40f 00d81f 00dc1f 00981f
28  00901f 00d00f 00881f 00e41f 00b01f 00d41f 00e81f 00e00f
30  00e81d 00cc0f 00801f 00941f 00ec1d 00f01d 00f41d 00f81d
38  00fc1d
```

There is no extra space at the end, so if additional sprites are needed, this table must be moved elsewhere in the ROM
and the code updated to use the new location. 
To update it to use the next available free space, `$02EFC2` in memory / `16FC2` in ROM, 
copy the range `1679b`-`16845` (inclusive) to `16FC2` (should overwrite values `FF FF FF ...`). 

Next, it's necessary to update the code to use the new address. It is referenced at `4497` in the ROM:
```asm
lda $02e79d,x ; Load last 8 bits from $02e79d + row ID * 3
pha
rep #$20
lda $02e79b,x ; Load first 16 bits from $02e79b + row ID * 3
```

Update `4497` to `BF C4 EF 02 48 C2 20 BF C2 EF 02` (should overwrite `BF 9D E7 02 48 C2 20 BF 9B E7 02`)

Now up to 7 additional entries can be placed at the end of the array.

At runtime when a row is loaded into VRAM, its position at `$742`+row ID is set to the VRAM row index.

# Animation functions?

At `$c371` a function is run from a vtable at `$c591` indexed by 2 * Sprite ID. These are the possible functions:

```
    0    1    2    3    4    5    6    7
0   53c6 7fc6 7fc6 7fc6 7fc6 7fc6 7fc6 7fc6
8   7fc6 7fc6 69c6 7fc6 7fc6 7bc6 7fc6 7fc6
10  7fc6 90c5 7fc6 90c5 a6c6 12c7 7fc6 d7c6
18  7fc6 7fc6 7fc6 7fc6 f4c6 f4c6 d7c6 73c7
20  3bc7 7fc6 7fc6 d7c6 7fc6 7fc6 7fc6 a6c6
28  a6c7 77c6 77c6 77c6 77c6 77c6 77c6 12c7
30  c0c7 a6c6 7fc6 46c8 7fc6 7fc6 7fc6 7fc6
38  7fc6 7fc6 7fc6 7fc6 90c5 90c5 90c5 90c5
40  c0c7 7fc6 69c6 7fc6 7fc6 32c8 50c6 50c6
48  50c6 50c6 41c6 48c6 50c6 50c6 50c6 50c6
```

These functions seem to determine the sprite animation state stored in `$7e8200` and later used by the rendering function.
Some functions store directions differently, e.g. for humans, Up, Right, Down, Left are `00`,`04`,`08`,`0c`, 
but for dragons they're `00`, `0C`, `14`, `18` 

# Rendering functions

Based on sprite ID, a rendering function is selected from a table in memory at `$a647` / from the ROM at `2647`. 

These functions are called from line `$a618` (function starts at `$a5a8`) and they write the sprite data to 
`$1300` which is later copied into OAM by HDMA.

These are the possible choices for the sprite IDs (note the addresses are little-endian):
```
    0    1    2    3    4    5    6    7
0   33a7 33a7 33a7 33a7 33a7 33a7 33a7 33a7
8   33a7 33a7 33a7 33a7 33a7 33a7 33a7 33a7
10  17a8 33a7 01a8 52ab d9ab bbab afa9 cbab
18  afa9 afa9 a9a9 a9a9 cbab 48ac d9ab d9ab
20  d9ab 03aa e2ab cbab afa9 a5a8 33a7 d9ab
28  33a7 33a7 33a7 afa9 33a7 33a7 33a7 faab
30  a7b0 cbab dba9 47b1 33a7 a5a8 1caa 17aa
38  2baa 21aa 26aa 82ab 87ab 8cab 79ab 91ab
40  a7b0 33a7 35ac 33a7 19a7 84a7 33a7 53a9
48  4aa9 33a7 12aa 33a7 2aa7 01a9 33a7 22a7
```

Semi-structured notes on these functions.
```
Fauna:
    52ab: Draw 8x8  directionless 2-frame from cols 5-5 e.g. insects
    01a8: Draw 8x16  mirrorable    1-frame from cols 4-5 e.g. giant rats
    17a8: Draw 8x16  mirrorable    1-frame from cols 2-3 e.g. mice
    48ac: Draw 16x8  directionless 4-frame from cols 6-7 e.g. gremlins
    33a7: Draw 16x16 4-direction   2-frame from cols 0-7 e.g. humans
    03aa: Draw 16x16 mirrorable    1-frame from cols 0-1 e.g. snakes
    a9a9: Draw 16x16 mirrorable    2-frame from cols 4-7 e.g. deer
    afa9: Draw 16x16 directionless 4-frame from cols 0-3 e.g. sea serpents
    bbab: Draw 16x16 directionless 4-frame from cols 4-7 e.g. giant squids
    d9ab: Draw 16x16 directionless 2-frame from cols 4-7 e.g. giant bats
    dba9: Draw 16x16 mirrorable    1-frame from cols 0-1 e.g. cats
    e2ab: Draw 16x16 4-direction   1-frame from cols 4-7 e.g. rabbits
    17aa: Draw 16x32 mirrorable    2-frame from cols 2-7 e.g. giant ants
    1caa: Draw 16x32 mirrorable    2-frame from cols 0-7 e.g. giant scorpions
    21aa: Draw 16x32 mirrorable    1-frame from cols 4-7 e.g. alligators
    26aa: Draw 16x32 mirrorable    2-frame from cols 0-7 e.g. horses
    2baa: Draw 16x32 mirrorable    2-frame from cols 2-7 e.g. cows
    a5a8: Draw 32x32 4-direction   2-frame from cols 0-7 4-rows e.g. gargoyle leaders, cyclops
    47b1: Draw dragons (48x48 plus-shaped)
    a7b0: Draw 48x48 directionless, limbed, 2/4-frame e.g. hydras and mystery monster #40
    faab: Draw wisps (3x 8x8 frames + 1 16x16 frame when casting)
Items:
    79ab: Draw 16x16 spidersilk from col 3
    91ab: Draw 16x8 sulfur ash from col 4 upper half
    82ab: Draw 16x8 blood moss from col 4 lower half
    87ab: Draw 16x8 mandrake root from col 5 upper half
    8cab: Draw 16x8 nightshade from col 6 upper half
Misc:
    19a7: Draw 16x16 directionless 2-frame from cols 0-1 e.g. sweeping man
    12aa: Draw 16x32 non-animated  overrides palette e.g. ship
    22a7: Draw 16x16 corpse from col 1 but weird behavior for other sprites
    2aa7: Draw 16x16 raft from col 4
    35ac: Draw 16x16 directionless 2-frame dead party member
    4aa9: Draw 32x32 directionless 1-frame from cols 4-7 e.g. gargoyle corpse
    53a9: Draw 32x32 directionless 1-frame from cols 1-3 e.g. cyclops corpse
    84a7: Draw 24x16 man in stocks 2-frame from cols 2-5 (actually two 16x16 sprites with overlap)
```

* `mirrorable` means that sprites exist for down/right directions, and up/left are mirrored from down/right
* `1-frame`/`2-frame`/`4-frame` refers to the number of animation frames used
* `cols 2-3` refers to which column in VRAM is used. Sprite data is loaded in in "rows" of 128x16 pixels, each "column" 
    is 16 pixels wide (except for the man in stocks, who has 2 24px wide animation frames across 3 columns)
* Some functions use a fixed palette, whereas others seem to select a palette based on sprite ID. 
* Animation behavior varies drastically based on render function, so e.g. alligators quickly alternate both tiles, 
    whereas cows slowly alternate only their head tile.
* For testing, Lord British's sprite ID can be updated at memory address `$7e800a`. Tile data is automatically loaded
    as needed, so this can be done while the game is running. 
    
    
# Reviving the silver serpent

It seems it was originally intended to have multiple segments that would follow the head, bend around corners, etc.
but that wasn't implemented for NES. Of the rendering functions available, there seem to be only 2 candidates:

## Render as 16x32 alligator

A head connected to a tail isn't as visually appealing, but is simple to do.

// TODO

## Render as a 16x48 dragon

This gives it a body, at least, but the wrong palette is used.
 
### Move the giant ant to another row
1. Update `4497` to `BF C4 EF 02 48 C2 20 BF C2 EF 02` (should overwrite `BF 9D E7 02 48 C2 20 BF 9B E7 02`)
2. Update `1676c` to `39` (should overwrite `2E`)
2. Copy the range `1679b`-`16845` (inclusive) to `16fc2`-`1706d` (should overwrite `FF FF FF ...`)
3. Update `1706e` to `00 F4 1F` (should overwrite `FF FF FF`)
4. Copy `fe800`-`febff` (inclusive) to `ff400` (should overwrite `FF FF FF ...`)

### Change the animation and render functions to the dragon functions

#### With palette fix:
1. Update `45F9` to `46 C8` (should overwrite `7F C6`)
2. Update `26af` to `D0 FB` (should overwrite `33 A7`)
3. Update `7bd0` to `A50438E9000485044C47B1` (should overwrite `FF FF FF ...`)

Source for new function:
```asm
    .m16
    lda $04
    sec
    sbc #$0400  ; Subtract 0004 so that palette flags 0008 (Palette 4) becomes 0004 (Palette 2) 
    sta $04
    jmp $b147 ; Jump to dragon render function
```

#### Without palette fix:

1. Update `45F9` to `46 C8` (should overwrite `7F C6`)
2. Update `26af` to `47 B1` (should overwrite `33 A7`)


### Rearrange the tiles into a dragon pattern

Insert the following at `fe400`:
```
000000000F001606290F200F350E300B000000000000090F1019101000041504000000000000B0004800B4A054D0B4600000000000000000B0B078C838689838
0000000000000000030005010A030C07000000000000000000000203040600040000000000000000C000A080D0C050C00000000000000000000040C020E02060
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
0E03050105010501050105010E030A030406020302030203020302030406040650C038E028E028E028E038E050C050C020601030103010301030103020602060
00000000000000001F003C1C5903650100000000000000000000031F2425020300000000000000000700FC00878778FF00000000000000000000070778FF0078
000000000F001100EE0F111FE0FF00FF0000000000000E0E101EE0F100E0000000000000F000C80014F04C780CF854B0000000000000B030081880C800088818
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
340F280F280F280F14070A030A030A030004101810181018080C0406040604069C3074F014F00CE038E050C050C050C048580878081818181030206020602060
1503180629072007280F280F14070A0308090D011011181810181018080C040668A028C034D014D014F014F028E050C010307010081828380818081810302060
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
0A030A031C07140714071C070A030A0304060406080C080C080C080C0406040650C070C0A080A080A080A08070C050C02060206040C040C040C040C020602060
0300010000000000000000000000000001010000000000000000000000000000407FCF0F78000F00000000000000000080C0707F0F0F00000000000000000000
01FEE2FE121FF70719000F0000000000000001E3E0F2181F0F0F000000000000A86050C0A8A0E8401000E000000000009030206070D0F090E0E0000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
0A030A030E03050105010501050106030406040604060203020302030203000250C050C050C070C020802080E080400020602060206020604040404040C08080
0A030A030A030E0304010401070102000406040604060406020202020203010150C050C070C0A080A080A080A08060C020602060206040C040C040C040C00040
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
0000000000000000C3007E00C3C33CFF00000000000000000000C3C33CFF003C0000000000007C00C7007C7C83FF00FF00000000000000007C7C83FF00830000
000000000000000000000000010003000000000000000000000000000000010100000000000000000F007800CF0F407F000000000000000000000F0F707F80C0
000000003C004300B630417E80FF05FD0000000000003C3C4B7982C0008002070000000000000000C000A08050C030E00000000000000000000040C020600020
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
0B0308020D040E040E0405000300000004070505020600040004020200000000C000800000000000000000000000000080800000000000000000000000000000
0300010000000000000000000000000001010000000000000000000000000000D0C01040B02070207020A000C000000020E0A0A0406000200020404000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00FFC3FF3C3CE7003C00000000000000000000C3C3FF3C3C00000000000000007CFF8383FE0083000000000000000000007C7CFF838300000000000000000000
650159033C1C1F00000000000000000002032425031F0000000000000000000078FF8787FC0007000000000000000000007878FF070700000000000000000000
00FF81FE4771BC3C43003C0000000000000002808AC9437F3C3C00000000000070E0D0C02000C0000000000000000000006020E0C0C000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
```

