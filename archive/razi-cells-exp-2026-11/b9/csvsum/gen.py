import random
random.seed(1)
cats=['c%02d'%i for i in range(50)]
out=['id,cat,val']
for i in range(2000000):
    out.append('%d,%s,%.2f'%(i,random.choice(cats),random.uniform(-100,100)))
open('data.csv','w').write('\n'.join(out)+'\n')
