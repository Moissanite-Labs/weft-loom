    if k & 1:
        t = -2; h = -1
    else:
        t = 2; h = 1
    for c in s[12:-1]:
        if c == '1':
            a, b = (a * b - h) % M, (b * b + t) % M
            t = -2; h = -1
        else:
            a, b = (a * a - t) % M, (a * b - h) % M
            t = 2; h = 1
    if s[-1] == '1':
        r = (b * (2 * b - a) + 2 * t + h) * 400000003 % M
    else:
        r = a * (2 * b - a) * 400000003 % M
    return -r % M if neg else r
if __name__ == "__main__":
    print(fib(int(sys.argv[1])))
