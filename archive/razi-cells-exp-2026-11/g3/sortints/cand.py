import sys
def main():
 import numpy as np
 d=sys.stdin.buffer.read()
 a=np.fromstring(d.decode(),dtype=np.int64,sep=' ')
 a.sort()
 r=str(a.tolist()).replace('[','',1)[:-1].encode()
 sys.stdout.buffer.write(r.translate(bytes.maketrans(b', ',b'

')).replace(b'\n\n',b'\n'))
main()
