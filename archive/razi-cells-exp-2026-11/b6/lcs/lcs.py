#!/usr/bin/env python3
"""Bit-parallel longest common subsequence length."""
import sys

def lcs_length(a, b):
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return 0
    if a == b:
        return len(b)
    alphabet = set(b)
    masks = {}
    if len(b) >= 256 and len(alphabet) <= 32:
        if b.isascii():
            reverse = b[::-1].encode('ascii')
            codes = {char: ord(char) for char in alphabet}
        else:
            codes = {char: i for i, char in enumerate(alphabet)}
            reverse = b[::-1].translate({ord(c): i for c, i in codes.items()}).encode('latin1')
        table = bytearray(b'0' * 256)
        for char, code in codes.items():
            table[code] = 49
            masks[char] = int(reverse.translate(table), 2)
            table[code] = 48
    else:
        for i, char in enumerate(b):
            masks[char] = masks.get(char, 0) | (1 << i)
    row = 0
    get = masks.get
    for char in a:
        matches = row | get(char, 0)
        row = matches & ((row << 1) - matches)
    return row.bit_count()

def main():
    a = sys.stdin.readline().rstrip('\r\n')
    b = sys.stdin.readline().rstrip('\r\n')
    print(lcs_length(a, b))

if __name__ == '__main__':
    main()
