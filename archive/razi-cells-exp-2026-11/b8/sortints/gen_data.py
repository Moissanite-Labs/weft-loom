import random, sys
random.seed(42)
# Generate 1,000,000 ints with a mix of ranges (negative, small, large 64-bit, etc.) or typical ints
# Let's check standard 32-bit/64-bit random ints
data = [str(random.randint(-10**9, 10**9)) for _ in range(1000000)]
with open("input.txt", "w") as f:
    f.write(" ".join(data[:500000]) + "\n" + "\n".join(data[500000:]) + "\n")
data_sorted = sorted( data, key=int )
with open("expected.txt", "w") as f:
    f.write("\n".join(data_sorted) + "\n")
