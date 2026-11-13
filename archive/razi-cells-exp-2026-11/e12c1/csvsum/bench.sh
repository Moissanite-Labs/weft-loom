s=$(date +%s.%N)
python3 csvsum.py < data.csv > out.txt
e=$(date +%s.%N)
head -c 0 out.txt
python3 -c "
import sys
d={}
for l in open('data.csv').readlines()[1:]:
    a=l.split(',');d[a[1]]=d.get(a[1],0)+float(a[2])
exp=''.join('%s %.2f\n'%(k,d[k]) for k in sorted(d))
print(0 if exp!=open('out.txt').read() else round(1/($e-$s),3))"
