import random
random.seed(7)
words = ["the","of","and","to","in","a","is","that","it","was","for","on","are","as","with","his","they","be","at","one"] + [f"w{i}" for i in range(5000)]
wts = [1/(i+1)**0.9 for i in range(len(words))]
# fast: draw a large pool once, then chunk into lines
pool = random.choices(words, wts, k=4_000_000)
out=[]; size=0; i=0
while size < 20_000_000:
    line = " ".join(pool[i:i+12]).capitalize() + ".\n"
    i = (i + 12) % (len(pool) - 12)
    out.append(line); size += len(line)
open("big.txt","w").write("".join(out))
