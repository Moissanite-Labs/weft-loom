    for p, c in zip(s[11:], s[12:-1]):
        if c == '1':
            if p == '1':
                a, b = (a * b + 1) % M, (b * b - 2) % M
            else:
                a, b = (a * b - 1) % M, (b * b + 2) % M
        elif p == '1':
            a, b = (a * a + 2) % M, (a * b + 1) % M
        else:
            a, b = (a * a - 2) % M, (a * b - 1) % M
    if s[-1] == '1':
        r = (b * (2 * b - a) + (-5 if s[-2] == '1' else 5)) * 400000003 % M
    else:
        r = a * (2 * b - a) * 400000003 % M
    return -r % M if neg else r
if __name__ == "__main__":
    print(fib(int(sys.argv[1])))
