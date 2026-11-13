import random, json, sys
sys.path.insert(0, '.')
import squeeze

random.seed(1234)
WORDS = "the of and to in a is that it was for on are as with his they at be this from have or by one had not but what all were when we there can an your which their said if do will each about how up out them then she many some so these would other into has more her two like him see time could no make than first been its who now people my made over did down only way find use may water long little very after words called just where most know".split()

def english(nwords):
    out = []
    for _ in range(nwords):
        w = random.choice(WORDS)
        if random.random() < 0.08:
            w = w.capitalize()
        if random.random() < 0.05:
            w += random.choice(['.', ',', ';', '!', '?'])
        out.append(w)
    return ' '.join(out)

def make_json(nitems):
    recs = []
    for i in range(nitems):
        recs.append({
            'id': i,
            'name': random.choice(WORDS) + ' ' + random.choice(WORDS),
            'email': random.choice(WORDS) + str(random.randint(1,999)) + '@example.com',
            'active': random.random() < 0.5,
            'score': round(random.uniform(0, 100), 3),
            'tags': [random.choice(WORDS) for _ in range(random.randint(0,3))],
            'nested': {'a': random.randint(-1000, 1000), 'b': None, 'c': english(3)},
        })
    return json.dumps(recs, indent=2)

parts = []
for _ in range(6):
    parts.append(english(random.randint(400, 1500)))
for _ in range(6):
    parts.append(make_json(random.randint(5, 40)))
data = '\n'.join(parts).encode('utf-8')

c = squeeze.compress(data)
d = squeeze.decompress(c)
assert d == data, 'ROUND TRIP FAIL'
ratio = len(data) / len(c)
print('orig=%d comp=%d ratio=%.4f' % (len(data), len(c), ratio))
print('RATIO %.6f' % ratio)
