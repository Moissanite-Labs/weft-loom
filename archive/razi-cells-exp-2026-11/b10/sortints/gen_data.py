import random

rng = random.Random(42)
# Mix of 1M integers: various ranges including negatives, 64-bit, small, duplicates
nums = [rng.randint(-10**9, 10**9) for _ in range(900000)]
nums.extend([rng.randint(-100, 100) for _ in range(90000)])
nums.extend([rng.randint(-10**18, 10**18) for _ in range(10000)])
rng.shuffle(nums)

# Write with mixed whitespace (spaces and newlines)
with open('input_1m.txt', 'w') as f:
    for i in range(0, len(nums), 10):
        f.write(' '.join(map(str, nums[i:i+10])) + '\n')

nums.sort()
with open('expected_1m.txt', 'w') as f:
    f.write('\n'.join(map(str, nums)) + '\n')
