import random,sys
random.seed(1)
n=int(sys.argv[1]) if len(sys.argv)>1 else 2000000
cats=["c%02d"%i for i in range(40)]
out=sys.stdout
out.write("id,cat,val\n")
w=out.write
for i in range(n):
    w("%d,%s,%.2f\n"%(i,cats[random.randrange(40)],random.random()*1000))
