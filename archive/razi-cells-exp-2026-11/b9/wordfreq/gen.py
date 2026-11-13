import random
random.seed(7)
words=[f"w{i}" for i in range(5000)]+["the","and","of","to","a","in","is","it","you","that"]*50
out=[]
n=0
while n<20_000_000:
    line=" ".join(random.choice(words) for _ in range(12))
    if random.random()<0.3: line=line.title()
    out.append(line); n+=len(line)+1
open("big.txt","w").write("\n".join(out)+"\n")
