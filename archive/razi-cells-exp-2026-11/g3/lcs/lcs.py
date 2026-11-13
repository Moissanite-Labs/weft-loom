import sys


def lcs_length(a: bytes, b: bytes) -> int:
    """Length of the longest common subsequence, bit-parallel (Hyyrö), list masks."""
    if len(a) > len(b):
        a, b = b, a
    m = len(a)
    if m == 0:
        return 0
    masks = [0] * 256
    for i, ch in enumerate(a):
        masks[ch] |= 1 << i
    full = (1 << m) - 1
    V = full
    for ch in b:
        U = V & masks[ch]
        V = (V + U) | (V - U)
    return m - (V & full).bit_count()


def main() -> None:
    data = sys.stdin.buffer
    a = data.readline().rstrip(b"\r\n")
    b = data.readline().rstrip(b"\r\n")
    sys.stdout.write(str(lcs_length(a, b)) + "\n")


if __name__ == "__main__":
    main()
