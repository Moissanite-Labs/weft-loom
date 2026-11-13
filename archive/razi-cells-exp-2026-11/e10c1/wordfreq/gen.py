import random, string
random.seed(7)
def mk(i):
    s=""
    while True:
        s+=string.ascii_lowercase[i%26]; i//=26
        if i==0: return s
words=[mk(i)+"x" for i in range(5000)]+["the","and","of","to","a","in","is","it","you","that"]
weights=[1]*5000+[2000]*10
toks=random.choices(words,weights,k=3_600_000)
lines=[" ".join(toks[i:i+12]) for i in range(0,len(toks),12)]
open("data.txt","w").write("\n".join(lines)+"\n")
