import sys,re,os
import sys as _sys
if len(_sys.argv) < 2: raise SystemExit('usage: make_variant.py WORKTREE_PATH')
WT = _sys.argv[1]
src=open(WT+'/scripts/e15_dual_morphogenesis.py').read()
def rep(a,b,cnt=1):
    global src
    assert src.count(a)==cnt,(a,src.count(a))
    src=src.replace(a,b)
rep("import numpy as np\n","import numpy as np\nimport os\nNOBIAS=os.environ.get('NOBIAS')=='1'\nRANDTEACHER=os.environ.get('RANDTEACHER')=='1'\nFULLREAD=os.environ.get('FULLREAD')=='1'\n")
rep("        blk = slice(w * width, (w + 1) * width)\n","        blk = slice(w * width, (w + 1) * width)\n        if RANDTEACHER:\n            blk = _perm[w*width:(w+1)*width]\n")
rep("    waves = []\n","    waves = []\n    _perm = np.random.default_rng(777+seed).permutation(20)\n")
rep("            # Step 2: Synaptic Corridor Routing","            if NOBIAS:\n                bias_residual = np.zeros_like(w_data['bias_vec'])\n            # Step 2: Synaptic Corridor Routing")
# control arm
rep('use_dinic_routing = mode in ("M1_synaptic_only", "M3_full_dual_morphogenesis")','use_dinic_routing = mode in ("M1_synaptic_only", "M3_full_dual_morphogenesis", "M4_ctrl")')
rep('use_synaptic_mitosis = mode in ("M1_synaptic_only", "M3_full_dual_morphogenesis")','use_synaptic_mitosis = mode in ("M1_synaptic_only", "M3_full_dual_morphogenesis", "M4_ctrl")')
rep("                else:\n                    if rec.scalar_gate_would_commit:","                else:\n                    if rec.scalar_gate_would_commit and (mode != 'M4_ctrl' or cand_ood_drift / (0.25 * base_ood_err) < 1.0):")
rep("            if use_mpdi_gate:\n                w_clean","            if use_mpdi_gate or mode == 'M4_ctrl':\n                w_clean")
rep("                assert rec_clean.mpdi_gate_commits\n","")
# readout
rep("            if use_dinic_routing or mode == \"M2_sensory_mpdi_fixed_dim\":","            if (use_dinic_routing or mode == \"M2_sensory_mpdi_fixed_dim\") and not FULLREAD:")
rep("            if poison_committed > 0:\n                ood_pred = xo @ w_mat","            if poison_committed > 0 or FULLREAD:\n                ood_pred = xo @ w_mat")
# mode lists
rep('''            for m in (
                "M0_fixed_scalar",
                "M1_synaptic_only",
                "M2_sensory_mpdi_fixed_dim",
                "M3_full_dual_morphogenesis",
            )''','''            for m in MODES''')
rep('''    modes = (
        "M0_fixed_scalar",
        "M1_synaptic_only",
        "M2_sensory_mpdi_fixed_dim",
        "M3_full_dual_morphogenesis",
    )''','''    modes = MODES''')
rep("def run_single_seed","MODES=('M0_fixed_scalar','M1_synaptic_only','M2_sensory_mpdi_fixed_dim','M3_full_dual_morphogenesis','M4_ctrl')\ndef run_single_seed")
open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'e15_var.py'),'w').write(src)
