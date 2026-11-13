#!/usr/bin/env python3
import csv, sys, io
from decimal import Decimal

def fallback(data):
    text=data.decode(sys.stdin.encoding or 'utf-8',sys.stdin.errors or 'strict')
    reader=csv.reader(io.StringIO(text,newline=None))
    header=next(reader,None)
    if header is None or [s.strip() for s in header]!=['id','cat','val']: raise ValueError('expected header id,cat,val')
    totals={}
    for _,cat,val in reader: totals[cat]=totals.get(cat,0)+Decimal(val)
    return [(cat,format(totals[cat],'.2f')) for cat in sorted(totals)]

def native(data):
    import ctypes as c
    import os, subprocess, tempfile
    class Entry(c.Structure):
        _fields_=[('offset',c.c_size_t),('length',c.c_size_t),('cents',c.c_int64),('hash',c.c_uint64)]
    base=os.path.dirname(os.path.abspath(__file__))
    src=os.path.join(base,'csvsum_native.c'); so=os.path.join(base,'csvsum_native.so')
    try:
        if not os.path.exists(so) or os.stat(src).st_mtime_ns>os.stat(so).st_mtime_ns:
            fd,tmp=tempfile.mkstemp(suffix='.so',dir=base);os.close(fd)
            try:
                subprocess.run(['cc','-O3','-std=c11','-shared','-fPIC',src,'-o',tmp],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                os.replace(tmp,so)
            finally:
                if os.path.exists(tmp):os.unlink(tmp)
        lib=c.CDLL(so)
    except (OSError,subprocess.SubprocessError):return None
    ptr=c.POINTER(Entry)();count=c.c_size_t()
    lib.sumcsv.argtypes=[c.c_char_p,c.c_size_t,c.POINTER(c.POINTER(Entry)),c.POINTER(c.c_size_t)]
    lib.sumcsv.restype=c.c_int
    lib.release_entries.argtypes=[c.POINTER(Entry)]
    if not lib.sumcsv(data,len(data),c.byref(ptr),c.byref(count)):return None
    try:
        rows=[]
        for i in range(count.value):
            e=ptr[i];cat=data[e.offset:e.offset+e.length].decode('utf-8');v=e.cents
            rows.append((cat,('-' if v<0 else '')+str(abs(v)//100)+'.'+str(abs(v)%100).zfill(2)))
        rows.sort()
        return rows
    finally:lib.release_entries(ptr)

def main():
    data=sys.stdin.buffer.read()
    rows=native(data)
    if rows is None:rows=fallback(data)
    csv.writer(sys.stdout,lineterminator='\n').writerows(rows)
if __name__=='__main__':main()
