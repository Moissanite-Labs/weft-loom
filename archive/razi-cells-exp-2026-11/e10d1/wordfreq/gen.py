import random
random.seed(42)
words=[f"w{i}" for i in range(5000)]+["the","of","and","to","a","in","is","it","you","that"]*50
weights=[1]*5000+[20]*500
lines=[" ".join(random.choices(words,weights,k=12))+".\n" for _ in range(20000)]
out=[];n=0
while n<20_000_000:
    s="".join(random.sample(lines,1000)); out.append(s); n+=len(s)
open("big.txt","w").write("".join(out))
