import os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'haar_tests.py')).read().split("print('A)")[0])
print('A2) commit rate by update norm and null-space energy fraction (dom delta -0.15 fixed); columns full / sub4, 100 trials')
for norm in [0.05,0.2,0.5,1.0,4.0]:
    for nf in [0,0.375,1.0]:
        c=[sum(gate(mk(nf,norm),m,ep=i) for i in range(100)) for m in (None,4)]
        print(f' norm={norm} null_frac={nf}: full={c[0]} sub4={c[1]}')
