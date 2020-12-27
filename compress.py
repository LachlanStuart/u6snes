#!/usr/bin/env python3
import argparse


def compress_rle(data):
    last_datum = None
    count = 0
    for datum in data:
        if datum == 0x81:
            yield 0x81
            yield 0x00
            # last_datum = None
            # count = 0
        elif datum == last_datum and count < 255:
            count += 1
        elif count >= 2:
            yield 0x81
            yield count + 1
            count = 0
            last_datum = datum
            yield datum
        else:
            for i in range(count):
                yield last_datum
            count = 0
            last_datum = datum
            yield datum

    if count >= 2:
        yield 0x81
        yield count + 1
    else:
        for i in range(count):
            yield last_datum


def compress_lzw(data):
    dictionary = []
    # init
    prev = data[0:1]
    prev_cw = 0
    yield 0x101, 0x100, b""
    yield 0x101, prev[0], prev
    data = data[1:]
    while len(data) > 0:
        # Brute-force search for the longest dictionary entry that prefixes data
        longest_i = 0
        longest_len = 0
        for i, string in enumerate(dictionary):
            if data.startswith(string) and len(string) > longest_len:
                longest_i = i
                longest_len = len(string)

        # The decompressor supports a special case when cw == cw_next it repeats the
        # last cw's string, then repeats the first byte of that string.
        if prev_cw >= 0x102:
            special = dictionary[prev_cw - 0x102]
            special = special + special[:1]
        else:
            special = None

        if (
            special is not None
            and len(special) >= longest_len
            and data.startswith(special)
        ):
            # The special case was better than a dictionary match, use it
            string = special
            cw = 0x102 + len(dictionary)
        elif longest_len:
            # Found a good dictionary match
            string = dictionary[longest_i]
            cw = 0x102 + longest_i
        else:
            # No dictionary match - emit the raw value
            string = data[0:1]
            cw = string[0]
        yield len(dictionary) + 0x102, cw, string
        dictionary.append(prev + string[0:1])
        prev = string
        prev_cw = cw
        data = data[len(string) :]

        if len(dictionary) + 0x102 >= 0x1000:
            # init
            prev = data[0:1]
            prev_cw = 0
            yield len(dictionary) + 0x102, 0x100, b""
            dictionary = []
            yield 0x101, prev[0], prev
            data = data[1:]

    yield len(dictionary) + 0x102, 0x101, b""


def write_lzw_debug_file(debug_file, lzw_strings):
    for cw_next, cw, string in lzw_strings:
        if cw == 0x100:
            continue
        clean_text = "".join(
            c if " " < c < "~" else "#"
            for c in string.decode("ascii", errors="replace")
        )
        debug_file.write(
            f"{cw_next: 4x}\t{cw: 4x}\t{string.hex().ljust(32)}\t{clean_text}\n"
        )


def pack_lzw_cws(lzw_strings):
    out = bytearray()
    res = 0
    res_bits = 0
    for cw_next, cw, string in lzw_strings:
        if cw_next < 0x200:
            cw_bits = 9
        elif cw_next < 0x400:
            cw_bits = 10
        elif cw_next < 0x800:
            cw_bits = 11
        elif cw_next < 0x1000:
            cw_bits = 12

        res |= cw << res_bits
        res_bits += cw_bits
        while res_bits >= 8:
            out.append(res.to_bytes(4, "little")[0])
            res_bits -= 8
            res = res >> 8
    while res_bits >= 0:
        out.append(res.to_bytes(4, "little")[0])
        res_bits -= 8
        res = res >> 8
    return bytes(out)


def parse_path_offset(path_and_offset):
    try:
        path, offset = path_and_offset.rsplit(":", maxsplit=1)
        if offset.startswith("0x"):
            offset = int(offset[2:], base=16)
        else:
            offset = int(offset)
        return path, offset
    except:
        return path_and_offset, None


def main(in_path, out_path, debug_path):
    in_path, in_offset = parse_path_offset(in_path)
    out_path, out_offset = parse_path_offset(out_path)
    in_file = open(in_path, "rb")
    if in_offset is not None:
        in_file.seek(in_offset)

    unpacked_bytes = in_file.read()
    print(f"Read {len(unpacked_bytes)} bytes")
    rle_bytes = bytes(bytearray(compress_rle(unpacked_bytes)))
    print(f"Compressed to {len(rle_bytes)} RLE bytes")
    lzw_strings = list(compress_lzw(rle_bytes))
    print(f"Compressed to {len(lzw_strings)} LZW codewords")
    if debug_path is not None:
        write_lzw_debug_file(open(debug_path, "wt"), lzw_strings)
        print("Wrote debug file")
    packed_bytes = pack_lzw_cws(lzw_strings)
    print(f"Compressed to {len(packed_bytes)} bytes")

    if out_offset is not None:
        out_data = bytearray(open(out_path, "rb").read())
        out_data[out_offset : out_offset + len(packed_bytes)] = packed_bytes
        open(out_path, "wb").write(out_data)
    else:
        open(out_path, "wb").write(packed_bytes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "in_path",
        help="Input file path, optionally suffixed by colon then a byte offset e.g. rom.sfc:0x80ff or rom.sfc:65535 (prefix with 0x for hex)",
    )
    parser.add_argument(
        "out_path",
        help="Output file path, optionally suffixed by colon then an offset to write a range into an existing file",
    )
    parser.add_argument(
        "--debug",
        nargs="?",
        help="(Optional) Path to write a debug file listing compressed strings",
    )
    args = parser.parse_args()
    main(args.in_path, args.out_path, args.debug)
