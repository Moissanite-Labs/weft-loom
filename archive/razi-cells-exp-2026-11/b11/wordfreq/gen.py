import random
random.seed(1)
words = ["the","of","and","to","a","in","is","it","you","that","he","was","for","on","are","with","as","I","his","they"] + [f"w{i}" for i in range(2000)]
weights = [50,30,28,25,22,20,15,14,13,12,11,10,9,8,7,6,5,4,3,2] + [1]*2000
out=[]; size=0
while size < 20_000_000:
    line = " ".join(random.choices(words, weights, k=12)) + ".\n"
    if random.random()<0.3: line=line.upper()
    out.append(line); size+=len(line)
open("data.txt","w").write("".join(out))
