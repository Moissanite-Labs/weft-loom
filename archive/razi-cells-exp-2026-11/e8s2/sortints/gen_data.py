import random

random.seed(42)
# Generate 1,000,000 integers (mix of ranges and negatives, whitespace separated)
data = [str(random.randint(-1000000000, 1000000000)) for _ in range(1000000)]
with open("input.txt", "w") as f:
    # mix spaces and newlines to test whitespace-separated
    for i in range(0, 1000000, 10):
        f.write(" ".join(data[i:i+10]) + "\n")

sdata = sorted(int(x) for x in data)
with open("expected.txt", "w") as f:
    f.write("\n".join(str(x) for x in sdata) + "\n")
