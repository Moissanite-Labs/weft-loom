import sys
nums = sorted(int(x) for x in sys.stdin.read().split())
sys.stdout.write('\n'.join(map(str, nums)) + '\n')
