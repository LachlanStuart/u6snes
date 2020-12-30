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

Palette ID comes from `f159` on ROM + sprite ID

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
    afa9: Draw 16x16 mirrorable    2-frame from cols 0-3 e.g. sea serpents
    bbab: Draw 16x16 directionless 2-frame from cols 4-7 e.g. giant squids
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
    
    
# Reviving the silver serpent

It seems it was originally intended to have multiple segments that would follow the head, bend around corners, etc.
but that wasn't implemented for NES. Of the rendering functions available, there seem to be only 2 candidates:

## Render as 16x32 alligator

A head connected to a tail isn't as visually appealing, but is simple to do.

// TODO

## Render as a 16x48 dragon

This gives it a body, at least.

Cons:
    * Giant ants need to be sacrificed or somehow relocated, as they share sprite data with the serpent 
    and the additional tiles are needed for the dragon renderer
    * The wrong palette is used, making it look like a copper/gold-colored serpent
 
// TODO
