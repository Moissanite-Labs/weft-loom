import random, json, sys, importlib
sys.path.insert(0, '.')
import squeeze

WORDS = ("the of and to in a is that for it as was with be by on not he I this are or his from at which but have an they you were her she all their one we there been has when who will more no if out so said what up its about into than them can only other new some could time these two may then do first any my now such like our over man me even most made after also did many before must through back years where much your way well down should because each just those people Mr how too little state good very make world still own see men work long get here between both life being under never day same another know while last might us great old year off come since against go came right used take three states himself few house use during without again place American around however home small found Mrs thought went say part once general high upon school every don't does got united left number course war until always away something fact though water less public put think almost hand enough far took head yet government system better set told nothing night end why called didn't eyes find going look asked later knew point next program city business give group toward young days let room president side social given present several order national possible rather second face per among form important often things looked early white case become large big need four within felt along children saw best church ever least power development light thing seemed family interest want members mind country area others turned although open god service certain kind problem began door different door sense history mean shall local car law life").split()

def english(rng, n):
    out = []
    while len(out) < n:
        k = rng.randint(5, 18)
        s = [rng.choice(WORDS) for _ in range(k)]
        s[0] = s[0].capitalize()
        out.append(' '.join(s) + rng.choice(['.', '.', '.', '!', '?', ',']))
        if rng.random() < 0.08:
            out.append('\n\n')
    return ' '.join(out)

def jsonish(rng, n):
    recs = []
    for i in range(n):
        recs.append({
            'id': i, 'name': rng.choice(WORDS) + ' ' + rng.choice(WORDS),
            'email': rng.choice(WORDS) + '@example.com',
            'active': rng.random() < 0.5, 'score': round(rng.random() * 100, 2),
            'tags': [rng.choice(WORDS) for _ in range(rng.randint(0, 5))],
            'address': {'city': rng.choice(WORDS).title(), 'zip': rng.randint(10000, 99999)},
            'notes': english(rng, rng.randint(0, 3)),
        })
    return json.dumps(recs, indent=2)

def corpus():
    rng = random.Random(12345)
    parts = []
    for i in range(6):
        parts.append(english(rng, 2500).encode())
        parts.append(jsonish(rng, 600).encode())
        parts.append(json.dumps([{'k%d' % j: rng.randint(0, 1000) for j in range(20)} for _ in range(300)]).encode())
    return parts

if __name__ == '__main__':
    tot_in = tot_out = 0
    for p in corpus():
        c = squeeze.compress(p)
        if squeeze.decompress(c) != p:
            print(0); sys.exit(1)
        tot_in += len(p); tot_out += len(c)
    print(round(tot_in / tot_out, 4))
