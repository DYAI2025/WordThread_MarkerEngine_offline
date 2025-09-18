# app/services/uncertainty_guard.py
"""
Intuition Package v3.3 - UNCERTAINTY Guardian Policy
Evidence mode enforcement when uncertainty intuition is confirmed
"""

def enforce_evidence_policy(ctx):
    """
    Tighten requirements when UNCERTAINTY intuition is confirmed.
    Example: require citations or trigger ask-for-evidence prompts.
    """
    ctx.runtime.policies.append({
        "id": "evidence_mode",
        "ttl": 5,
        "description": "Require evidence/grounding for claims",
        "triggers": ["uncertainty_confirmed"],
        "effects": [
            "require_citations",
            "down_rank_ungrounded_claims", 
            "auto_prompt_for_sources"
        ]
    })

def check_evidence_requirements(ctx, claim):
    """
    Check if claim meets evidence requirements under uncertainty policy
    """
    if any(p["id"] == "evidence_mode" for p in ctx.runtime.policies):
        if not has_evidence_markers(claim):
            return False, "Evidence required due to uncertainty context"
    return True, "Evidence check passed"

def has_evidence_markers(claim):
    """
    Check if claim contains evidence/grounding markers
    Add your specific evidence detection logic here
    """
    evidence_patterns = [
        "according to",
        "research shows",
        "studies indicate", 
        "data suggests",
        "source:",
        "reference:",
        "cite:",
        "proven by"
    ]
    
    claim_text = claim.get('text', '').lower()
    return any(pattern in claim_text for pattern in evidence_patterns)

def process_uncertainty_confirmation(ctx, clu):
    """
    Hook to call when CLU_INTUITION_UNCERTAINTY is confirmed
    Add this call inside process_intuition_clu after confirmation
    """
    if clu.id == "CLU_INTUITION_UNCERTAINTY" and clu.state == "confirmed":
        enforce_evidence_policy(ctx)
        ctx.annotate(clu, note="Evidence policy activated")

# Integration example for intuition_runtime.py:
# 
# In process_intuition_clu function, after clu.state = "confirmed":
# if family(clu) == "uncertainty":
#     from .uncertainty_guard import process_uncertainty_confirmation
#     process_uncertainty_confirmation(ctx, clu)
