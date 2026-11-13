import sys, os
def _fast():
    here = os.path.dirname(os.path.abspath(__file__))
    exe = os.path.join(here, 'csvsum_c')
    src = os.path.join(here, 'csvsum.c')
    try:
        if not os.path.exists(exe) or (os.path.exists(src) and os.path.getmtime(src) > os.path.getmtime(exe)):
            import subprocess
            tmp = exe + '.%d' % os.getpid()
            try:
                subprocess.check_call(['cc', '-O3', '-march=native', '-pthread', '-o', tmp, src], stderr=subprocess.DEVNULL)
            except Exception:
                subprocess.check_call(['cc', '-O2', '-pthread', '-o', tmp, src], stderr=subprocess.DEVNULL)
            os.replace(tmp, exe)
        os.execv(exe, [exe])
    except Exception:
        pass
def main():
    from decimal import Decimal
    d = {}
    f = sys.stdin.buffer
    f.readline()
    for line in f:
        p = line.split(b',')
        if len(p) < 3: continue
        try: d[p[1]] = d.get(p[1], 0) + Decimal(p[2].strip().decode())
        except Exception: pass
    w = sys.stdout.write
    for k in sorted(d):
        w('%s %.2f\n' % (k.decode(), d[k]))
if not os.environ.get('CSVSUM_PURE'):
    _fast()
main()
