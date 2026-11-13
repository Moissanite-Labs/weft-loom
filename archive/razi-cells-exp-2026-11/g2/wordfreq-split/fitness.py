import sys, os, time, re, subprocess, tempfile, random
from collections import Counter

def reference(text):
    words = re.findall(r'[a-z]+', text.lower())
    c = Counter(words)
    top = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    return ''.join('%s %d\n' % (w, n) for w, n in top)

def main():
    random.seed(202406)
    vocab = ['alpha','beta','gamma','delta','epsilon','zeta','eta','theta','iota','kappa','lambda','mu','nu','xi','omicron','pi','rho','sigma','tau','upsilon','phi','chi','psi','omega'] + ['w%d' % i for i in range(200)]
    target = 20 * 1024 * 1024
    tmp = tempfile.NamedTemporaryFile(delete=False, dir='.')
    path = tmp.name
    total = 0
    try:
        while total < target:
            ws = [random.choice(vocab) for _ in range(10000)]
            for i in range(0, len(ws), 11):
                ws[i] = ws[i].upper()
            s = ' '.join(ws) + '. '
            b = s.encode()
            tmp.write(b)
            total += len(b)
        tmp.close()
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        expected = reference(text)
        with open(path, 'rb') as f:
            start = time.perf_counter()
            p = subprocess.run([sys.executable, 'wf.py'], stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            elapsed = time.perf_counter() - start
        out = p.stdout.decode('utf-8', errors='replace')
        if p.returncode != 0 or out != expected:
            sys.stderr.write('INCORRECT\n')
            sys.stderr.write(p.stderr.decode('utf-8', errors='replace') + '\n')
            sys.stderr.write('expected:\n' + expected + '\nout:\n' + out + '\n')
            print(0)
        else:
            print(1.0 / elapsed if elapsed > 0 else 0)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass

if __name__ == '__main__':
    main()
