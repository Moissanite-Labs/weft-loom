import re, subprocess, sys
from collections import Counter

def ref(text):
    low = text.lower()
    parts = re.split(r'[^a-z]+', low)
    c = Counter(p for p in parts if p)
    return sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]

data = open('corpus.txt','rb').read()
exp = ref(data.decode('utf-8','replace'))
got = subprocess.run([sys.executable,'wf.py'], input=data, capture_output=True).stdout.decode()
g = [(l.rsplit(' ',1)[0], int(l.rsplit(' ',1)[1])) for l in got.strip().split('\n') if l]
print("expected:", exp)
print("got     :", g)
print("MATCH" if g == exp else "MISMATCH")
