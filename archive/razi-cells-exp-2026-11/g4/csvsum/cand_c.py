import sys, pandas as pd
df = pd.read_csv(sys.stdin.buffer, dtype={'cat': object})
g = df.groupby('cat', sort=True)['val'].sum()
sys.stdout.write('\n'.join(c+','+format(v,'.2f') for c,v in g.items())+'\n')
