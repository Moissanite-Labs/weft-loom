## results_tf.json: 12 hosts, 18839 weights

| Prediction | Hosts on which it holds | Verdict |
|---|---|---|
| H1a_top_over_rand_ge_10 | 12 of 12 | confirmed |
| H1b_perm_far_and_silent | 12 of 12 | confirmed |
| H2a_fisher_within_1p1_on_fit_probes | 12 of 12 | confirmed |
| H2b_fisher_within_1p25_on_held | 10 of 12 | mixed |
| H3a_fisher_blind_to_null_moves | 12 of 12 | confirmed |
| H3b_fisher_off_by_3_on_a_natural_move | 12 of 12 | confirmed |
| H4_probe_within_1p25_on_held | 9 of 12 | mixed |
| H5a_blind_adversary_ratio_ge_10 | 12 of 12 | confirmed |
| H5b_blind_adversary_breaks_bar_under_graft_level | not tested | not tested |
| H6a_adv_breaks_10x_before_rand | 12 of 12 | confirmed |
| H6b_one_step_ge_r_break_adv | 12 of 12 | confirmed |
| H6c_graft_passes_at_r_ge_20 | not tested | not tested |
| H6d_rand_breaks_inside_shipped_radius | not tested | not tested |
| H7_cert_le_attack | not tested | not tested |

| Class of move | Breaking radius, median (range) | Safe size at change 0.05, median |
|---|---|---|
| adam_novel | 0.65 (0.3 to 1) | 0.0107 |
| adv | 0.1 (0.1 to 0.1) | 0.00234 |
| adv_blind | 1 (0.3 to 1) | 0.0153 |
| flip | never broken | 0.0928 |
| grad_native | 0.2 (0.1 to 0.3) | 0.00421 |
| grad_novel | 0.3 (0.3 to 1) | 0.0061 |
| null | never broken | 0.149 |
| rand | 3 (3 to 3) | 0.0592 |
| top | 0.1 (0.1 to 0.1) | 0.00226 |

| Move at its own length | Distance | Fisher prediction | Change on probes | Change held-out | Drop |
|---|---|---|---|---|---|
| finetune_joint | 6.66 | 3.78 | 2.9 | 2.92 | 0, passes 12 of 12 |
| flip | 14.9 | 8.05 | 8.05 | 8.04 | 1 |
| one_step | 0.137 | 0.619 | 0.624 | 0.641 | 0 |
| perm | 17.1 | 20.1 | 3.53e-15 | 3.47e-15 | 0 |
| to_init | 13.3 | 17.2 | 4.04 | 4.04 | 0.96 |

wrote results_tf.summary.json
