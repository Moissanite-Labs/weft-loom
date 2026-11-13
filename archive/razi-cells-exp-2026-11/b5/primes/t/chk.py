import sys; sys.path.insert(0,'t')
from pre import count_primes
def ref(n):
    s=bytearray([1])*max(n,2); s[0]=s[1]=0
    for i in range(2,int(n**0.5)+1):
        if s[i]: s[i*i::i]=bytes(len(range(i*i,n,i)))
    return s[:n].count(1)
for Q in [(7,11,13),(7,11,13,17),(7,11,13,17,19)]:
    bad=[n for n in list(range(0,4000))+[10**5,10**6] if count_primes(n,Q)!=ref(n)]
    print(Q, 'bad' if bad else 'ok', bad[:5])
print(count_primes(5000000), count_primes(10**8))
