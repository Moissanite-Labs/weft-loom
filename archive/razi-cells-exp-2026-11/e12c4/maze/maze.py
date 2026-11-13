import sys
def main():
    lines=sys.stdin.read().split()
    h=len(lines);w=len(lines[0])
    g=''.join(lines)
    s=g.find('S');e=g.find('E')
    if s<0 or e<0:print(-1);return
    dist=bytearray(h*w)  # visited
    dist[s]=1
    fr=[s];d=0
    blocked=g.encode()
    while fr:
        if dist[e]:break
        d+=1;nx=[]
        for p in fr:
            x=p%w
            if p>=w:
                q=p-w
                if not dist[q] and blocked[q]!=35:dist[q]=1;nx.append(q)
            if p+w<h*w:
                q=p+w
                if not dist[q] and blocked[q]!=35:dist[q]=1;nx.append(q)
            if x:
                q=p-1
                if not dist[q] and blocked[q]!=35:dist[q]=1;nx.append(q)
            if x<w-1:
                q=p+1
                if not dist[q] and blocked[q]!=35:dist[q]=1;nx.append(q)
        fr=nx
    print(d if dist[e] else -1)
main()
