"""
app.py
------
Gradio UI. For now it works WITHOUT LLM agents:
  form -> ClaimFacts -> code routing -> parallel evidence gathering -> result.
Later, Person B's agent pipeline replaces `extract_facts_placeholder`
(free text -> ClaimFacts) and the summary step.
"""

import asyncio
from datetime import date

import gradio as gr
from pydantic import ValidationError

from src.schemas import ClaimFacts, IncidentType, Route
from tools import claims_tools as ct
from tools.routing import assess_risk

INCIDENT_CHOICES = [i.value for i in IncidentType]


# ---------- Step 1: build ClaimFacts (SEAM: Person B's intake agent goes here) ----------
def extract_facts_placeholder(policy_number, incident_type, incident_date, amount, description, police_report):
    """Turns form fields into validated ClaimFacts. Raises ValueError with a friendly message."""
    parsed_date = None
    if incident_date and incident_date.strip():
        try:
            parsed_date = date.fromisoformat(incident_date.strip())
        except ValueError:
            raise ValueError("Incident date must be in YYYY-MM-DD format, e.g. 2026-06-01.")
    try:
        return ClaimFacts(
            policy_number=(policy_number or "").strip().upper() or None,
            incident_type=incident_type,
            incident_date=parsed_date,
            description=(description or "").strip(),
            estimated_amount_egp=amount if amount else None,
            police_report_mentioned=bool(police_report),
        )
    except ValidationError as e:
        problems = "; ".join(f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors())
        raise ValueError(f"Invalid claim data -> {problems}")


# ---------- Step 3: parallel evidence gathering (asyncio.gather) ----------
async def gather_evidence(facts: ClaimFacts) -> dict:
    pn, it = facts.policy_number, facts.incident_type.value
    policy, coverage, history, docs = await asyncio.gather(
        asyncio.to_thread(ct.get_customer_policy, pn),
        asyncio.to_thread(ct.get_policy_coverage, pn, it),
        asyncio.to_thread(ct.check_claim_history, pn),
        asyncio.to_thread(ct.check_required_documents, pn, it),
    )
    estimate = None
    if facts.estimated_amount_egp is not None:
        estimate = ct.calculate_deductible(pn, facts.estimated_amount_egp)
    return {"policy": policy, "coverage": coverage, "history": history, "docs": docs, "estimate": estimate}


def _ok(x) -> bool:
    return not isinstance(x, dict)  # tools return {"error": ...} on failure


def format_evidence(ev: dict) -> str:
    lines = ["### Evidence (from tools)"]
    p, c, h, d, e = ev["policy"], ev["coverage"], ev["history"], ev["docs"], ev["estimate"]

    lines.append(f"- **Policy:** {p.customer_name}, {p.vehicle}, status `{p.status}`, valid {p.start_date} → {p.end_date}"
                 if _ok(p) else f"- **Policy:** ⚠️ {p['error']}")
    lines.append(f"- **Coverage:** {'covered' if c.is_covered else 'NOT covered'}, limit {c.coverage_limit_egp:,.0f} EGP, deductible {c.deductible_egp:,.0f} EGP"
                 if _ok(c) else f"- **Coverage:** ⚠️ {c['error']}")
    lines.append(f"- **History:** {h.previous_claims_count} previous claims, {h.claims_last_12_months} in last 12 months"
                 if _ok(h) else f"- **History:** ⚠️ {h['error']}")
    if _ok(d):
        lines.append(f"- **Documents:** missing → {', '.join(d.missing) if d.missing else 'nothing missing'}")
    else:
        lines.append(f"- **Documents:** ⚠️ {d['error']}")
    if e:
        lines.append(f"- **Estimate (informational only, not a promise):** {e['estimated_payable_egp']:,.0f} EGP"
                     if "error" not in e else f"- **Estimate:** ⚠️ {e['error']}")
    return "\n".join(lines)


# ---------- Main handler ----------
async def process_claim(policy_number, incident_type, incident_date, amount, description, police_report):
    try:
        facts = extract_facts_placeholder(policy_number, incident_type, incident_date, amount, description, police_report)
    except ValueError as e:
        return f"❌ {e}", "", ""

    risk = assess_risk(facts)  # deterministic Python, no LLM
    routing_md = (
        f"### Routing (code-orchestrated)\n"
        f"- **Risk level:** `{risk.risk_level.value}`\n"
        f"- **Route:** `{risk.route.value}`\n"
        f"- **Reasons:** {'; '.join(risk.reasons) if risk.reasons else 'none'}"
    )

    if risk.route == Route.HUMAN_REVIEW:
        status = ("🛑 **Escalated: a human adjuster must handle this claim.**\n\n"
                  "No case was created automatically and no decision was made.")
        return status, routing_md, ""

    try:
        evidence = await gather_evidence(facts)
    except Exception as e:  # reliability: never crash the UI
        return f"❌ Evidence gathering failed: {type(e).__name__}. Please retry.", routing_md, ""

    case = ct.create_claim_case(facts.policy_number, facts.incident_type.value, facts.description)
    if "error" in case:
        status = f"⚠️ Evidence gathered, but the case was not created: {case['error']}"
    else:
        status = (f"✅ Case `{case['case_id']}` created with status `{case['status']}`.\n\n"
                  "A human adjuster will make the final coverage decision.")
    return status, routing_md, format_evidence(evidence)


# ---------- UI ----------
EXAMPLES = [
    ["POL-1001", "collision", "2026-06-01", 15000, "Rear-ended at a traffic light, bumper damaged.", True],   # happy path
    ["POL-1002", "collision", "2026-06-01", 9000, "Side mirror broken in a parking lot.", False],            # frequent claimant
    ["POL-1003", "collision", "2025-06-01", 12000, "Hit a barrier on the ring road.", True],                 # expired
    ["POL-1005", "theft", "2026-06-01", 80000, "Car stolen from the street overnight.", True],               # not covered
    ["POL-1006", "collision", "2026-06-01", 250000, "Major crash on the highway, front end destroyed.", True],  # huge amount
    ["POL-9999", "collision", "2026-06-01", 5000, "Scratched by another car while parked.", False],          # unknown policy
]

with gr.Blocks(title="Insurance Claims Assessment") as demo:
    gr.Markdown("# 🚗 Car Insurance Claims Assessment\n"
                "Prepares a file for a **human adjuster**. It never approves or rejects a claim.")
    with gr.Row():
        with gr.Column():
            policy_in = gr.Textbox(label="Policy number", placeholder="POL-1001")
            incident_in = gr.Dropdown(INCIDENT_CHOICES, value="collision", label="Incident type")
            date_in = gr.Textbox(label="Incident date (YYYY-MM-DD)", placeholder="2026-06-01")
            amount_in = gr.Number(label="Estimated damage (EGP)", value=None)
            desc_in = gr.Textbox(label="What happened?", lines=4)
            police_in = gr.Checkbox(label="Police report available")
            btn = gr.Button("Assess claim", variant="primary")
        with gr.Column():
            status_out = gr.Markdown()
            routing_out = gr.Markdown()
            evidence_out = gr.Markdown()

    inputs = [policy_in, incident_in, date_in, amount_in, desc_in, police_in]
    btn.click(process_claim, inputs=inputs, outputs=[status_out, routing_out, evidence_out])
    gr.Examples(EXAMPLES, inputs=inputs, label="Demo scenarios (click one, then press Assess claim)")

if __name__ == "__main__":
    demo.launch()