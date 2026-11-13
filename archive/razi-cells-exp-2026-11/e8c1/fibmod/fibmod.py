import sys
from _fibmod import fib

if __name__ == '__main__':
    if len(sys.argv) > 1:
        print(fib(int(sys.argv[1])))
