import sys
import re
from collections import Counter

WORD_RE = re.compile(rb'[a-z]+')

def main():
    data = sys.stdin.buffer.read()
    words = WORD_RE.findall(data.lower())
    counts = Counter(words)
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    out = ''.join('%s %d\n' % (w.decode('ascii'), n) for w, n in top)
    sys.stdout.write(out)

if __name__ == '__main__':
    main()
