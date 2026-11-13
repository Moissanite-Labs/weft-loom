
## split 1
A: Write sortints.py as pure Python: read sys.stdin.buffer, split on whitespace, map ints, list.sort(), then write '\n'.join(map(str, nums)) with trailing newline.
B: Write sortints.py as a thin wrapper that replaces itself with a shell pipeline: os.execvp('sh', ['sh','-c', "LC_ALL=C tr -s '[:space:]' '\\n' | LC_ALL=C sort -n"]) to convert whitespace to newlines th
medians A=1.7362 B=0.74371 over 5 runs; kept A
loser lesson: - Lost mainly to overhead: `tr | sort -n` is an external line-based pipeline, and `sort -n` reparses text instead of sorting native integers once in memory.
- `sort -n` also isn’t arbitrary-precision, so huge Python ints can be misordered.
- Keep `LC_ALL=C`, buffered binary I/O, and the `os.execvp` thin-wrapper idea—but use an in-process integer/radix sort, not external `sort -n`.
loser body kept at .lineage/1-b/
