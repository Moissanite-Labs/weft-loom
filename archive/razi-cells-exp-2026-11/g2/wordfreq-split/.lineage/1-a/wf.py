import sys, re
from collections import Counter

def main():
    data = sys.stdin.buffer.read()
    text = data.decode('utf-8', errors='replace').lower()
    words = re.findall(r'[a-z]+', text)
    c = Counter(words)
    top = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    out = '\n'.join('%s %d' % (w, n) for w, n in top)
    if out:
        sys.stdout.write(out + '\n')

main()
