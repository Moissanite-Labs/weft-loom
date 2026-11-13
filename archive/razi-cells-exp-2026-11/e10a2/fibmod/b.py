    o = k & 1
    for c in s[12:-1]:
        if c == '1':
            if o:
                a, b = (a * b + 1) % M, (b * b - 2) % M
            else:
                a, b = (a * b - 1) % M, (b * b + 2) % M
                o = 1
        elif o:
            a, b = (a * a + 2) % M, (a * b + 1) % M
            o = 0
        else:
            a, b = (a * a - 2) % M, (a * b - 1) % M
    if s[-1] == '1':
        r = (b * (2 * b - a) + (-5 if o else 5)) * 400000003 % M
    else:
        r = a * (2 * b - a) * 400000003 % M
    return -r % M if neg else r
if __name__ == "__main__":
    print(fib(int(sys.argv[1])))
