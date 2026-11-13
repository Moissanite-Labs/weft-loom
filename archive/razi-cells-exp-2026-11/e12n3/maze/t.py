import sys
sys.path.insert(0,'.')
from maze import solve
# small check
assert solve(["S.#","..#","#.E"])==4
assert solve(["S#E"])==-1
import time
t=time.time();r=solve(open('maze.txt').read().split());d=time.time()-t
print(1/d if r!=0 else 0)
