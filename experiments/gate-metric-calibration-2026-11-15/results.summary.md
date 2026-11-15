## results.json: 12 hosts, 12488 weights

| Prediction | Hosts on which it holds | Verdict |
|---|---|---|
| H1a_top_over_rand_ge_10 | 12 of 12 | confirmed |
| H1b_perm_far_and_silent | 12 of 12 | confirmed |
| H2a_fisher_within_1p1_on_fit_probes | 12 of 12 | confirmed |
| H2b_fisher_within_1p25_on_held | 12 of 12 | confirmed |
| H3a_fisher_blind_to_null_moves | 12 of 12 | confirmed |
| H3b_fisher_off_by_3_on_a_natural_move | 12 of 12 | confirmed |
| H4_probe_within_1p25_on_held | 12 of 12 | confirmed |
| H5a_blind_adversary_ratio_ge_10 | 12 of 12 | confirmed |
| H5b_blind_adversary_breaks_bar_under_graft_level | 12 of 12 | confirmed |
| H6a_adv_breaks_10x_before_rand | 12 of 12 | confirmed |
| H6b_one_step_ge_r_break_adv | 12 of 12 | confirmed |
| H6c_graft_passes_at_r_ge_20 | 11 of 12 | confirmed |
| H6d_rand_breaks_inside_shipped_radius | 12 of 12 | confirmed |
| H7_cert_le_attack | 12 of 12 | confirmed |

| Class of move | Breaking radius, median (range) | Safe size at change 0.05, median |
|---|---|---|
| adam_novel | 1 (1 to 1) | 0.103 |
| adv | 0.3 (0.1 to 0.3) | 0.0149 |
| adv_blind | 3 (3 to 10) | 0.39 |
| dormant | 10 (10 to 10) | 1.29 |
| flip | 1 (1 to 1) | 0.0802 |
| grad_native | 0.3 (0.3 to 0.3) | 0.0258 |
| grad_novel | 0.3 (0.3 to 1) | 0.0411 |
| null | 10 (10 to 10) | 1.84 |
| rand | 3 (3 to 3) | 0.339 |
| top | 0.3 (0.1 to 0.3) | 0.0149 |

| Move at its own length | Distance | Fisher prediction | Change on probes | Change held-out | Drop |
|---|---|---|---|---|---|
| finetune_joint | 8.74 | 0.659 | 0.275 | 0.266 | 0.0016, passes 12 of 12 |
| flip | 6.6 | 4.26 | 4.26 | 4.17 | 3.63 |
| graft | 28.1 | 1 | 0.214 | 0.21 | 0.017, passes 11 of 12 |
| one_step | 1.01 | 0.482 | 0.455 | 0.463 | 0.0593 |
| perm | 29.2 | 7.31 | 1.09e-15 | 1.07e-15 | 0 |
| to_init | 12.5 | 3.11 | 2.3 | 2.27 | 1.11 |

wrote results.summary.json
