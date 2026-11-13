from sys import argv
M=1000000007
a=0
b=1
for c in bin(int(argv[1]))[2:]:
    t=a*(2*b-a)%M
    u=(a*a+b*b)%M
    if c=='1':a,b=u,(t+u)%M
    else:a,b=t,u
print(a)
