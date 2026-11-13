import random, sys
random.seed(42)
words = ["the","of","and","to","in","a","is","that","for","it","as","was","with","be","by","on","not","he","I","this","are","or","his","from","at","which","but","have","an","had","they","you","were","their","one","all","we","can","her","has","there","been","if","more","when","will","would","who","so","no"] + [f"w{i}" for i in range(2000)]
weights = [1000/(i+1) for i in range(len(words))]
out = []
size = 0
target = 20_000_000
while size < target:
    line = " ".join(random.choices(words, weights, k=12))
    if random.random() < 0.3: line = line.capitalize() + "."
    if random.random() < 0.1: line = line.replace(" ", ", ", 1)
    out.append(line)
    size += len(line) + 1
sys.stdout.write("\n".join(out) + "\n")
