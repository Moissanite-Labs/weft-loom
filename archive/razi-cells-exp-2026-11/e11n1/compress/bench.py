import random, json, sys
sys.path.insert(0, '.')
from squeeze import compress, decompress
random.seed(1)
w = "the of and to in is that it was for on are with as his they be at one have this from or had by hot but some what there we can out other were all your when up use word how said an each she which do their time if will way about many then them write would like so these her long make thing see him two has look more day could go come did number sound no most people my over know water than call first who may down side been now find".split()
txt = " ".join(random.choice(w) for _ in range(150000)).encode()
js = json.dumps([{"id": i, "name": random.choice(w), "tags": [random.choice(w) for _ in range(3)], "v": random.random()} for i in range(5000)]).encode()
tot = 0; comp = 0
for d in (txt, js):
    c = compress(d)
    if decompress(c) != d:
        print(0); sys.exit()
    tot += len(d); comp += len(c)
print(tot / comp)
