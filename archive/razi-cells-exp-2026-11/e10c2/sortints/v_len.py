import sys, os
d = sys.stdin.buffer.read().split()
neg = [t for t in d if t[0] == 45]
pos = [t for t in d if t[0] != 45]
neg.sort(reverse=True); neg.sort(key=len, reverse=True)
pos.sort(); pos.sort(key=len)
neg += pos
os.write(1, b"\n".join(neg) + b"\n")
