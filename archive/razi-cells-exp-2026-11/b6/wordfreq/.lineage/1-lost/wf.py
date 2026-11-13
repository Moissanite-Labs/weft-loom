import sys,re,heapq,multiprocessing as mp
from collections import Counter
TEXT=''
def count_range(bounds):
    start,stop=bounds
    counts=Counter()
    while start<stop:
        end=TEXT.find(' ',start+262144,stop)
        if end<0: end=stop
        counts.update(TEXT[start:end].split()); start=end+1
    return counts

def main():
    global TEXT
    text=sys.stdin.read()
    if text.isascii():
        TEXT=text.translate({c:c+32 if 65<=c<=90 else c if 97<=c<=122 else 32 for c in range(128)})
        if len(TEXT)>2000000 and 'fork' in mp.get_all_start_methods():
            bounds=[]; start=0
            while start<len(TEXT):
                end=TEXT.find(' ',start+len(TEXT)//8)
                if end<0: end=len(TEXT)
                bounds.append((start,end)); start=end+1
            with mp.get_context('fork').Pool(8) as pool: parts=pool.map(count_range,bounds)
            counts=Counter()
            for part in parts: counts.update(part)
        else: counts=count_range((0,len(TEXT)))
    else: counts=Counter(re.findall('[a-z]+',text.lower()))
    for w,n in heapq.nsmallest(10,counts.items(),key=lambda p:(-p[1],p[0])): print(w,n)
if __name__=='__main__': main()
