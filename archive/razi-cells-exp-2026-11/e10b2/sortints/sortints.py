# sortints: read whitespace-separated ints from stdin, print sorted, one per line.
# Fast path: exec a compiled C helper (sortints_c, built from sortints_c.c: radix sort + custom itoa).
# Fallback (no compiler / helper fails to start): numpy implementation in sortints_np.py.
import os, sys
def main():
    d = os.path.dirname(os.path.abspath(__file__))
    b = os.path.join(d, 'sortints_c'); c = b + '.c'
    if not os.environ.get('SORTINTS_NO_C'):
        try:
            if not os.path.exists(b) or (os.path.exists(c) and os.path.getmtime(c) > os.path.getmtime(b)):
                import subprocess
                tmp = b + '.%d.tmp' % os.getpid()
                subprocess.run(['cc', '-O2', '-o', tmp, c], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                os.replace(tmp, b)
            os.execv(b, [b])
        except Exception:
            pass
    import sortints_np
main()
