# app/services/intuition_runtime.py
"""
Intuition Package v3.3 Runtime Hook
Lean-Deep adaptive learning for CLU_INTUITION markers
~70 LOC core; state machine + adaptive rules; non-intrusive to schema.
"""
import re

ATLEAST_RE = re.compile(r"AT_LEAST\s+(\d+)\s+(?:DISTINCT\s+)?(?:SEMs?\s+)?IN\s+(\d+)\s+messages", re.I)
ONEOF_RE   = re.compile(r"AT_LEAST\s+1\s+of\s+\[([A-Z0-9_,\s]+)\]\s+IN\s+confirm_window", re.I)

def parse(rule):
    match = ATLEAST_RE.search(rule)
    return tuple(map(int, match.groups())) if match else (2, 5)

def parse_targets(rule):
    m = ONEOF_RE.search(rule or "")
    return set(t.strip() for t in (m.group(1).split(",") if m else []) if t.strip())

# helpers bound by engine
last_n   = lambda ctx,n: ctx.window.last_n(n)     # iterable of marker matches
next_n   = lambda ctx,n: ctx.window.next_n(n)
any_in   = lambda it,ids: any(m.id in ids for m in it)
count_d  = lambda it,ids: len({m.id for m in it if m.id in ids})
family   = lambda clu: clu.id.replace("CLU_INTUITION_","" ).lower()

# side effects

def apply_multiplier(ctx, fam, m, ttl):
    """Apply confidence multiplier for intuition family"""
    ctx.runtime.multipliers.append({"family": fam, "m": m, "ttl": ttl})

def loosen_activation(clu):
    """Reduce activation threshold when precision is high"""
    X,Y = parse(clu.activation["rule"])
    clu.activation["rule"] = f"AT_LEAST {X} DISTINCT SEMs IN {Y+1} messages"

def tighten_activation(clu):
    """Increase activation threshold when precision is low"""
    X,Y = parse(clu.activation["rule"])
    clu.activation["rule"] = f"AT_LEAST {X+1} DISTINCT SEMs IN {max(3,Y)} messages"

def broaden_targets(clu):
    """Expand confirmation targets when system is performing well"""
    ids = ", ".join(clu.composed_of)
    clu.metadata["intuition"]["confirm_rule"] = f"AT_LEAST 1 of [{ids}] IN confirm_window"

def harden_targets(clu):
    """Narrow confirmation targets to high-confidence markers"""
    hard = [s for s in clu.composed_of if any(k in s for k in ("ESCALATION","SADNESS","COMMITMENT","VALIDATION"))]
    subset = ", ".join((hard[:2] or clu.composed_of[:1]))
    clu.metadata["intuition"]["confirm_rule"] = f"AT_LEAST 1 of [{subset}] IN confirm_window"

# main processing function

def process_intuition_clu(ctx, clu):
    """
    Main intuition processing function for contextual_rescan phase
    Call this for each CLU with tag 'intuition' at end of Phase-3
    """
    fam_ids = set(clu.composed_of)
    X,Y = parse(clu.activation["rule"])             # X of Y
    
    # Check if activation threshold is met
    if count_d(last_n(ctx,Y), fam_ids) >= X:
        clu.state = "provisional"
        ctx.annotate(clu, note="INT provisional")
        
        # Confirmation phase
        confN = int(clu.metadata["intuition"]["confirm_window"])
        targets = parse_targets(clu.metadata["intuition"]["confirm_rule"]) or fam_ids
        
        if any_in(next_n(ctx, confN), targets):
            # Intuition confirmed
            clu.state = "confirmed"
            ctx.telemetry.inc(clu.metadata["telemetry_keys"]["counter_confirmed"])
            m = float(clu.metadata["intuition"]["multiplier_on_confirm"])
            apply_multiplier(ctx, family(clu), m, ttl=confN)
            ctx.annotate(clu, note=f"INT confirmed (x{m})")
        else:
            # Decay phase - check if family signals continue
            decN = int(clu.metadata["intuition"]["decay_window"])
            if not any_in(next_n(ctx, decN), fam_ids):
                clu.state = "decayed"
                ctx.telemetry.inc(clu.metadata["telemetry_keys"]["counter_retracted"])
                ctx.annotate(clu, note="INT decayed")

        # Online adaptation based on precision metrics
        keyC = clu.metadata["telemetry_keys"]["counter_confirmed"]
        keyR = clu.metadata["telemetry_keys"]["counter_retracted"]
        keyE = clu.metadata["telemetry_keys"]["ewma_precision"]
        
        c = ctx.telemetry.get(keyC, 0)
        r = ctx.telemetry.get(keyR, 0)
        prec = c / max(1, c+r)
        ewma = ctx.telemetry.update_ewma(keyE, prec, alpha=0.2)
        
        # Adaptive threshold adjustment
        if   ewma >= 0.70: 
            loosen_activation(clu)
            broaden_targets(clu)
        elif ewma <  0.50: 
            tighten_activation(clu)
            harden_targets(clu)

def contextual_rescan_hook(ctx):
    """
    Integration hook for Phase-3 contextual_rescan
    Call this at the end of your contextual processing
    """
    for marker in ctx.active_markers:
        if hasattr(marker, 'tags') and 'intuition' in marker.tags:
            if marker.id.startswith('CLU_INTUITION_'):
                process_intuition_clu(ctx, marker)
