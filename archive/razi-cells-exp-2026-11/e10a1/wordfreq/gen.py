import random
random.seed(42)
base = ["the","of","and","to","in","a","is","that","it","was","for","on","with","as","be","at","by","this","had","not"]
extra = ["w%s" % "".join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(random.randint(2,9))) for _ in range(20000)]
words = base + extra
weights = [1.0/(i+1) for i in range(len(words))]
out = []
size = 0
target = 20*1024*1024
seps = [" "," "," "," ",", ",". ","\n","; "," - "]
while size < target:
    chunk = random.choices(words, weights, k=50000)
    parts = []
    for w in chunk:
        r = random.random()
        if r < 0.1: w = w.capitalize()
        elif r < 0.12: w = w.upper()
        parts.append(w)
        parts.append(random.choice(seps))
    s = "".join(parts)
    out.append(s); size += len(s)
open("text.txt","w").write("".join(out))
