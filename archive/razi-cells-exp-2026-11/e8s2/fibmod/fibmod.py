import sys

MOD = 1_000_000_007
PISANO = 2_000_000_016

# Precompute 2 tables of size 65536 (16-bit chunks)!
# Since n % 2_000_000_016 < 2^31, n fits in two 16-bit chunks: low 16 bits (0..65535) and high 15 bits (0..30517).
def _build_tables():
    mod = 1_000_000_007
    # T0: F_k and F_{k+1} for k in 0..65536
    F0 = [0] * 65537
    F0[1] = 1
    for i in range(2, 65537):
        F0[i] = (F0[i - 1] + F0[i - 2]) % mod
    # Wait: for high chunk h = n >> 16, s = h << 16, h in 0..30517
    # F_{s + low} = (F_{low} * F_{s-1} + F_{low+1} * F_s) % mod !
    # Notice if low == 0, F_0 = 0, F_1 = 1 -> 0 * F_{s-1} + 1 * F_s = F_s!
    # So we only need F0[low], F0[low+1], and for high chunk h we need F_{s-1} and F_s!
    # Step for s = 65536:
    f_step_m1 = F0[65535]
    f_step = F0[65536]
    f_step_p1 = (f_step_m1 + f_step) % mod

    T1_m1 = [0] * 30518
    T1_0 = [0] * 30518
    # For h = 0 (s = 0): F_{-1} = 1, F_0 = 0
    cur_m1, cur_0 = 1, 0
    for h in range(30518):
        T1_m1[h] = cur_m1
        T1_0[h] = cur_0
        # advance by 65536:
        # new_0 = cur_0 * f_step_m1 + cur_1 * f_step
        # where cur_1 = cur_m1 + cur_0
        cur_1 = (cur_m1 + cur_0) % mod
        nxt_0 = (cur_0 * f_step_m1 + cur_1 * f_step) % mod
        nxt_1 = (cur_0 * f_step + cur_1 * f_step_p1) % mod
        cur_m1 = (nxt_1 - nxt_0) % mod
        cur_0 = nxt_0

    return F0, T1_m1, T1_0

_F0, _T1_m1, _T1_0 = _build_tables()

def fib(n: int, mod: int = 1_000_000_007, F0=_F0, T1_m1=_T1_m1, T1_0=_T1_0) -> int:
    if n <= 0:
        return 0
    n %= 2_000_000_016
    low = n & 0xFFFF
    high = n >> 16
    return (F0[low] * T1_m1[high] + F0[low + 1] * T1_0[high]) % mod

if __name__ == "__main__":
    print(fib(int(sys.argv[1])))
