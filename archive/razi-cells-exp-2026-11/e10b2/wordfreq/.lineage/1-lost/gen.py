import random
random.seed(12345)
base = ['the','of','and','to','in','a','is','that','for','it','as','was','with','be','by','on','not','he','this','are','or','his','from','at','which','but','have','an','had','they','you','were','their','one','all','we','can','her','has','there','been','if','more','when','will','would','who','so','no']
words = base + ['w' + ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(random.randint(2,8))) for _ in range(5000)]
weights = [1.0/(i+1) for i in range(len(words))]
seps = [' ',' ',' ',' ',', ','. ','\n','; ',' - ','! ','\t', ' 42 ', "'"]
out = []
size = 0
target = 20*1024*1024
while size < target:
    ws = random.choices(words, weights, k=20000)
    ss = random.choices(seps, k=20000)
    parts = []
    for w, s in zip(ws, ss):
        r = random.random()
        if r < 0.1: w = w.capitalize()
        elif r < 0.13: w = w.upper()
        parts.append(w); parts.append(s)
    chunk = ''.join(parts)
    out.append(chunk); size += len(chunk)
open('big.txt','w').write(''.join(out))
