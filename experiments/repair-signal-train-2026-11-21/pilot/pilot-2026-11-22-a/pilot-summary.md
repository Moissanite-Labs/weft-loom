# Pilot summary

Run pilot-2026-11-22-a, status complete.

| Gate | Result |
|---|---|
| adapter_pass_rate_testable | true |
| forced_opening_accepted | true |
| format_breaks_low | true |
| go | false |
| no_new_block_in_replies | true |
| projected_time_ok | false |

| Model | Passed | Failed the check | Broke the format |
|---|---|---|---|
| base | 31 | 67 | 2 |
| adapter | 50 | 50 | 0 |

Sampling: 200 calls, 514538026582 ns in total. Training: 8 steps, 56389111251 ns in total.

| Spend | Tokens | Dollars |
|---|---|---|
| cached_prefill | 0 | 0 |
| prefill | 68218 | 102327/10000000 |
| sample | 7381 | 7381/2000000 |
| train | 96688 | 18129/250000 |

Total spent: 108049/1250000 dollars, ceiling 1/2, planned 924487/10000000.
