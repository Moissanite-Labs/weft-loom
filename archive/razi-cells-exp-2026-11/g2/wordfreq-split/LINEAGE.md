
## split 1 (TIE: within noise)
A: Implement wf.py by reading all stdin bytes, decoding UTF-8 with errors='replace', lowercasing the full string, then using the compiled str regex [a-z]+ and collections.Counter to count words; sort by 
B: Implement wf.py by reading all stdin bytes, calling bytes.lower() directly, then using a compiled bytes regex [a-z]+ to extract words without any decode; decode each matched word (ASCII) for output an
medians A=1.71523 B=1.73339 over 5 runs; kept A
loser lesson: It paid for a full extra `bytes.lower()` copy and `findall` list, then sorted all unique words instead of only selecting top 10.  
Keep: stay in bytes, avoid unnecessary whole-input copies, and use `heapq.nsmallest(10, counts.items(), key=...)` for top-k with ties.  
Only decode/format the final words, not during counting.
loser body kept at .lineage/1-b/
