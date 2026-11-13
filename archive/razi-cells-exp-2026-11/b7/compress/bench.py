"""Fitness assay: round-trip correctness + compression ratio on the fixed mix."""
import gen_data, squeeze

def main():
    data = gen_data.make_corpus(64)
    blob = squeeze.compress(data)
    if squeeze.decompress(blob) != data:
        print(0)
        return
    extra = (b"", b"a", b"\x00\xff\x00" * 40, bytes(range(256)) * 5,
             data[:137], data[-271:], b'{"a":1,"b":[true,null,1.25]}')
    for t in extra:
        if squeeze.decompress(squeeze.compress(t)) != t:
            print(0)
            return
    print("%.6f" % (len(data) / len(blob)))

main()
