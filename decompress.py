#!/usr/bin/env python3
import argparse
MAX_CW_SIZE = 12
CW_MASK = [2 ** i - 1 for i in range(16)]

def iter_codewords(stream):
  bits_read = 0
  buf = 0
  buf_len = 0
  stream = stream
  cw_size = 9
  cw_next = 0x102

  while True:
    addr = bits_read
    bits_read += cw_size
    while buf_len < cw_size:
      buf = buf | int.from_bytes(stream.read(1), 'little') << buf_len
      buf_len += 8
    cw = buf & CW_MASK[cw_size]
    buf = buf >> cw_size
    buf_len -= cw_size

    if cw == 0x100:
      # print(f'At {addr:04x} reinit')
      cw_size = 9
      cw_next = 0x101 # This is one less than 0x102 because the next cw is written directly and doesn't count
      yield addr, None, cw
    elif cw == 0x101:
      return
    else:
      assert cw <= cw_next, (cw, cw_next)
      yield addr, cw_next, cw
      cw_next += 1

      if cw_next >= (1 << cw_size):
        if cw_size + 1 <= MAX_CW_SIZE:
          # print(f'At {addr:04x} increased cw_size to {cw_size + 1} bits')
          cw_size += 1
        else:
          # print(f'At {addr:04x} cw_size got too big. Next command should be reinit.')
          pass


def decompress_lzw(codewords):
  def get_dict_string(cw):
    result = b''
    while cw > 0xff:
      char, cw = dictionary[cw - 0x102]
      result = char + result
    result = cw.to_bytes(1, 'little') + result
    return result

  dictionary = [] # Codeword 0x0102 corresponds to self.dictionary[0]
  pw = 0 # previous cw
  for addr, cw_next, cw in codewords:
    # print(f'At {addr:04x}: {cw}')
    if pw == 0x100:
      # Last codeword was a reset - this codeword skips the dictionary completely
      yield addr, cw_next, cw, cw.to_bytes(1, 'little')
    elif cw == 0x100:
      dictionary = []
    else:
      if cw < cw_next:
        # Normal case - cw is either a dictionary entry (>0x102) or a literal value
        string = get_dict_string(cw)
        yield addr, cw_next, cw, string
      else:
        # Special case - use last cw's string, then repeat the first byte.
        # Don't think too hard about it. It saves bytes, it doesn't need to make sense.
        # This case isn't used in some files, but it's used by the title screen data.
        string = get_dict_string(pw)
        yield addr, cw_next, cw, string + string[0:1]

      dictionary.append((string[0:1], pw))

    pw = cw

def extract_data_from_lzw_lines(lzw_strings):
  return b''.join(string for addr, cw_next, cw, string in lzw_strings)

def write_lzw_debug_file(debug_file, lzw_strings):
  for addr, cw_next, cw, string in lzw_strings:
    clean_text = ''.join(c if ' ' < c < '~' else '#' for c in string.decode("ascii", errors="replace"))
    debug_file.write(
      # f'{addr: 8x}\t'
      f'{cw_next: 4x}\t{cw: 4x}\t'
      f'{string.hex().ljust(32)}\t{clean_text}\n'
    )

def decompress_rle(data):
  rle_on = False
  last_datum = b'\0'
  result = bytearray()
  for datum in data:
    if rle_on:
      rle_on = False
      if datum == 0:
        # print(f'Escaped 0x81')
        result.append(0x81)
      else:
        # print(f'RLE! {last_datum} * {datum}')
        for i in range(datum - 1):
          result.append(last_datum)
    elif datum == 0x81:
      rle_on = True
    else:
      result.append(datum)
      last_datum = datum

  return bytes(result)


def parse_path_offset(path_and_offset):
  try:
    path, offset = path_and_offset.rsplit(':', maxsplit=1)
    if offset.startswith('0x'):
      offset = int(offset[2:], base=16)
    else:
      offset = int(offset)
    return path, offset
  except:
    return path_and_offset, None


def main(in_path, out_path, debug_path):
  in_path, in_offset = parse_path_offset(in_path)
  out_path, out_offset = parse_path_offset(out_path)
  in_file = open(in_path, 'rb')
  if in_offset is not None:
    in_file.seek(in_offset)
  else:
    in_offset = 0

  codewords = list(iter_codewords(in_file))
  offset_after = in_file.tell()
  print(f'Read {len(codewords)} codewords from {in_offset:06x}-{offset_after:06x} ({offset_after-in_offset} bytes)')
  lzw_strings = list(decompress_lzw(codewords))
  print(f'Decompressed LZW to {len(lzw_strings)} strings')
  if debug_path is not None:
    write_lzw_debug_file(open(debug_path, 'wt'), lzw_strings)
    print('Wrote debug file')

  lzw_bytes = extract_data_from_lzw_lines(lzw_strings)
  print(f'Decompressed LZW to {len(lzw_bytes)} bytes')
  out_data = decompress_rle(lzw_bytes)
  print(f'Decompressed RLE to {len(out_data)} bytes')

  if out_offset is not None:
    out_file = open(out_path, 'w+b')
    out_file.seek(out_offset)
  else:
    out_file = open(out_path, 'wb')
  out_file.write(out_data)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument(
    'in_path', help='Input file path, optionally suffixed by colon then a byte offset e.g. rom.sfc:0x80ff or rom.sfc:65535 (prefix with 0x for hex)'
  )
  parser.add_argument(
    'out_path', help='Output file path, optionally suffixed by colon then an offset to write a range into an existing file'
  )
  parser.add_argument('--debug', nargs='?', help='(Optional) Path to write a debug file listing compressed strings')
  args = parser.parse_args()
  main(args.in_path, args.out_path, args.debug)

  # offset = 0x48000 # Avatar, Lord British, etc
  # offset = 0x28060 # Intro
