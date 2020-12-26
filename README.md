# u6snes
Command-line tools for working with data files in Ultima 6 on the SNES

# Decompressing LZW data
```
usage: decompress.py [-h] [--debug [DEBUG]] in_path out_path

positional arguments:
  in_path          Input file path, optionally suffixed by colon then a byte
                   offset e.g. rom.sfc:0x80ff or rom.sfc:65535 (prefix with 0x
                   for hex)
  out_path         Output file path, optionally suffixed by colon then an
                   offset to write a range into an existing file

optional arguments:
  -h, --help       show this help message and exit
  --debug [DEBUG]  (Optional) Path to write a debug file listing compressed
                   strings
```

Known offsets of data files inside the USA Ultima 6 ROM:
* `0x28060` - the title screen
* `0x48000` - the first dialog file (contains dialog for the Avatar, companions, Lord British, etc.)

# Compressing LZW data
```
usage: compress.py [-h] [--debug [DEBUG]] in_path out_path

positional arguments:
  in_path          Input file path, optionally suffixed by colon then a byte
                   offset e.g. rom.sfc:0x80ff or rom.sfc:65535 (prefix with 0x
                   for hex)
  out_path         Output file path, optionally suffixed by colon then an
                   offset to write a range into an existing file

optional arguments:
  -h, --help       show this help message and exit
  --debug [DEBUG]  (Optional) Path to write a debug file listing compressed
                   strings
```

# Modding workflow
```
# Make a copy of your ROM to write modifications to
cp u6.sfc u6_modded.sfc

# Extract dialog file
./decompress.py u6.sfc:0x48000 dialog1.raw

# Make changes to dialog1.raw

# Reinsert dialog file into modded ROM
./compress.py dialog1.raw u6_modded.sfc:0x48000
```
