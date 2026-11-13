import json
import random
import time
import squeeze

def corpus():
    r = random.Random(871209)
    names = ['Ada', 'Ben', 'Chloe', 'David', 'Elena', 'Felix', 'Grace', 'Hugo', 'Iris', 'Jules', 'Kai', 'Lena']
    places = ['harbor', 'garden', 'library', 'station', 'market', 'school', 'valley', 'museum']
    verbs = ['visited', 'studied', 'remembered', 'described', 'discovered', 'restored', 'surveyed', 'photographed']
    adjectives = ['quiet', 'ancient', 'bright', 'unusual', 'familiar', 'distant', 'busy', 'peaceful']
    words = ('the a an of in on with without before after across near through and but because although when while it they we this that was is will might could should have had been very quite more less some many few every another each other small large new old good long short early late day night year time work life world people water light tree road house city river story book friend idea question answer different important possible simple careful together again always never often sometimes slowly quickly').split()
    blocks = []
    for i in range(2400):
        name, place = r.choice(names), r.choice(places)
        text = f'{name} {r.choice(verbs)} the {r.choice(adjectives)} {place}. '
        text += ' '.join(r.choice(words) for _ in range(r.randrange(30, 65))) + '.\n'
        record = {'id': i, 'name': name, 'location': place, 'active': r.random() < .7,
                  'score': round(r.uniform(0, 1000), 3), 'tags': r.sample(words, 4),
                  'notes': text.strip(), 'measurements': [r.randrange(10000) for _ in range(5)]}
        blocks.append(text.encode())
        blocks.append((json.dumps(record, ensure_ascii=False) + '\n').encode())
    return b''.join(blocks)

def check():
    r = random.Random(112)
    for b in [b'', b'a', bytes(range(256)), b'\0'*10000, b'abc'*10000, r.randbytes(10001), 'Hello, 世界! 🌍'.encode()]:
        assert squeeze.decompress(squeeze.compress(b)) == b

if __name__ == '__main__':
    try:
        check()
        raw = corpus()
        start = time.monotonic()
        packed = squeeze.compress(raw)
        assert squeeze.decompress(packed) == raw
        # Keep the assay long enough for meaningful evaluation, independent of startup.
        while time.monotonic() - start < .3:
            assert squeeze.decompress(packed) == raw
        print(len(raw) / len(packed))
    except Exception:
        print(0)
