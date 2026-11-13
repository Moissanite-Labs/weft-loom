import hashlib, json, pathlib
import numpy as np

N = 1_000_000
SEED = 0x5EED2025

def dump_case(name, values):
    a = np.asarray(values, dtype=np.int64)
    text = ('\n'.join(map(str, a.tolist())) + '\n').encode('ascii')
    pathlib.Path(name).write_bytes(text)
    ordered = np.sort(a)
    out = ('\n'.join(map(str, ordered.tolist())) + '\n').encode('ascii')
    return {
        'file': name,
        'n': int(a.size),
        'input_bytes': len(text),
        'output_bytes': len(out),
        'sha256': hashlib.sha256(out).hexdigest(),
    }

rng = np.random.default_rng(SEED)
# Common benchmark: signed 32-bit ints, with duplicates and boundary values.
a = rng.integers(-(1 << 31), (1 << 31), size=N, dtype=np.int64)
a[:1000] = rng.integers(-1000, 1001, size=1000, dtype=np.int64)
a[1000:1010] = [-(1 << 31), (1 << 31) - 1, 0, -1, 1,
                -(1 << 31), (1 << 31) - 1, -999, 999, 0]
# Stress benchmark: full signed 64-bit range, including both endpoints.
b = np.frombuffer(rng.bytes(N * 8), dtype='<i8').astype(np.int64, copy=True)
b[0] = -(1 << 63)
b[1] = (1 << 63) - 1
b[2] = 0
b[3] = -1
b[4] = 1

meta = {'seed': SEED, 'cases': [dump_case('bench_i32.txt', a),
                                dump_case('bench_i64.txt', b)]}

edge = b'  +3\t-0\n\n9223372036854775807 -9223372036854775808  +00012 \r\n 3  -1  '
nums = sorted(map(int, edge.split()))
edge_out = ('\n'.join(map(str, nums)) + '\n').encode('ascii') if nums else b''
pathlib.Path('edge_in.txt').write_bytes(edge)
pathlib.Path('edge_out.txt').write_bytes(edge_out)
pathlib.Path('empty_in.txt').write_bytes(b' \t\r\n\n')

pathlib.Path('bench_meta.json').write_text(json.dumps(meta, indent=2) + '\n')
print(json.dumps(meta, indent=2))
