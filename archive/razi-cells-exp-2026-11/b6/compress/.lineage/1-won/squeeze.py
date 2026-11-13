import lzma,re,struct
from collections import Counter
RX=re.compile(rb'[A-Za-z]+ ?')
CODES=bytes(list(range(128,254))+list(range(1,9))+list(range(14,32))+list(range(65,91))+list(range(97,123)))
def compress(data):
 raw=b'R'+lzma.compress(data)
 counts=Counter(re.findall(rb'[A-Za-z]+',data));words=[w for w,c in counts.most_common() if c>1][:len(CODES)]
 table={w:bytes([CODES[i]]) for i,w in enumerate(words)};used=set(CODES[:len(words)])|{254,255}
 trans=[bytes([255,c]) if c in used else bytes([c]) for c in range(256)]
 def lit(s):return b''.join(trans[c] for c in s)
 out=[];p=0
 for m in RX.finditer(data):
  s=m[0];space=s.endswith(b' ');w=s[:-1] if space else s
  out.append(lit(data[p:m.start()]));out.append((b'' if space else b'\xfe')+table[w] if w in table else lit(s));p=m.end()
 out.append(lit(data[p:]));header=bytes([len(words)])+b''.join(struct.pack('<I',len(w))+w for w in words)
 coded=b'T'+lzma.compress(header+b''.join(out));return min((raw,coded),key=len)
def decompress(data):
 if data[:1]==b'R':return lzma.decompress(data[1:])
 if data[:1]!=b'T':raise ValueError('format')
 src=lzma.decompress(data[1:]);n=src[0];p=1;table={}
 for i in range(n):
  size=struct.unpack_from('<I',src,p)[0];p+=4;table[CODES[i]]=src[p:p+size];p+=size
 out=[]
 while p<len(src):
  c=src[p];p+=1
  if c==255:out.append(src[p:p+1]);p+=1
  elif c==254:out.append(table[src[p]]);p+=1
  elif c in table:out.append(table[c]+b' ')
  else:out.append(bytes([c]))
 return b''.join(out)
