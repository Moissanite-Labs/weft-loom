import json
c=json.load(open("/Users/kethuda/Work/weft-loom-20261113/experiments/e13-geodesic-shunting-plasmid-2026-11-12/e13_certificates.json"))
ps=c["per_seed"]
pre=ps["arms"]["pre_graft_host"]["shifted_native_r2"]
for arm in ["A2_gfpt_flat_no_retraction","A4_gfpt_shunting_geodesic","A3_gfpt_geodesic_excitatory_only"]:
    nat=ps["arms"][arm]["shifted_native_r2"]; nov=ps["arms"][arm]["shifted_novel_r2"]
    drops=[p-n for p,n in zip(pre,nat)]
    print(arm, f"max nat drop={max(drops):.4f} (bar 0.025)  min novel={min(nov):.4f} (bar 0.70, donor min {min(ps['donor_shifted_novel_r2']):.4f}) passes={sum(1 for d,v in zip(drops,nov) if d<=0.025 and v>=0.70)}/12")
print("A2 novel mean > A4:", c["single_graft_arms"]["A2_gfpt_flat_no_retraction"]["shifted_novel_r2_mean"], c["single_graft_arms"]["A4_gfpt_shunting_geodesic"]["shifted_novel_r2_mean"])
print("A4 native mean - A2:", round(c["single_graft_arms"]["A4_gfpt_shunting_geodesic"]["shifted_native_r2_mean"]-c["single_graft_arms"]["A2_gfpt_flat_no_retraction"]["shifted_native_r2_mean"],4))
# multigen gated: is monotonic trivial? each gen adds a skill so denominator changes?
g=ps["multigen_gated_shifted_r2"]
print("gated per-gen means:", [round(sum(g[str(i)])/12,4) for i in range(4)])
