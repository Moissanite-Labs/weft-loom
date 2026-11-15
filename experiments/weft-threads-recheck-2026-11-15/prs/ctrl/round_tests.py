from fractions import Fraction
from weft.runtime.plasm.synaptic_flow import certify_cost_partitioned_dual, verify_fraction_dual_certificate
def t(name,**kw):
    try:
        c=certify_cost_partitioned_dual(**kw); print(name,'-> CERTIFIED', c.remaining_budget_q, c.partitioned_drift_q, verify_fraction_dual_certificate(c)['ok'])
    except Exception as e: print(name,'-> rejected:',type(e).__name__,str(e)[:70])
t('overspend 10 x 1.0000004 vs budget 10',initial_budget=Fraction(10),step_costs=[1.0000004]*10,quotient_drifts=[0.1]*10,drift_cap=Fraction(3,4))
t('drift 0.7500004 vs cap 3/4',initial_budget=Fraction(20),step_costs=[1.0]*5,quotient_drifts=[0.7500004]*5,drift_cap=Fraction(3,4))
t('cost 1e-9 x 3 budget 0 (true spend>0)',initial_budget=Fraction(0),step_costs=[1e-9]*3,quotient_drifts=[0.1]*3,drift_cap=Fraction(3,4))
