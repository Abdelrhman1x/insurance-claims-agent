import json
import re

from agents import (
    GuardrailFunctionOutput,
    input_guardrail,
    output_guardrail,
    tool_input_guardrail,
    ToolGuardrailFunctionOutput,
)

INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous|prior|above) (instructions|rules)",
    r"disregard (the )?(system|previous) (prompt|instructions)",
    r"reveal (your |the )?(system )?prompt",
    r"you are now",
    r"(approve|accept) (my|this) claim",
    r"تجاهل (كل )?(التعليمات|الأوامر)",
    r"وافق على (المطالبة|الطلب)",
]

OFF_TOPIC_HINT = r"(insurance|claim|policy|car|accident|وثيقة|تأمين|عربية|حادث|مطالبة|سيارة|POL-)"

FORBIDDEN_OUTPUT = [
    r"claim (is|has been|was) (approved|rejected|denied)",
    r"(we|the company|insurer) (will|shall) (pay|compensate|reimburse)",
    r"you will (be paid|receive|get)",
    r"approved for payment",
    r"تمت الموافقة",
    r"سيتم (تعويضك|دفع)",
]


def _text(inp) -> str:
    if isinstance(inp, str):
        return inp
    return " ".join(str(i.get("content", "")) for i in inp if isinstance(i, dict))


# ---------- 1) Input guardrail ----------
@input_guardrail
async def input_safety_guardrail(ctx, agent, user_input) -> GuardrailFunctionOutput:
    text = _text(user_input)
    reasons = [p for p in INJECTION_PATTERNS if re.search(p, text, re.IGNORECASE)]
    if not re.search(OFF_TOPIC_HINT, text, re.IGNORECASE):
        reasons.append("off_topic")
    return GuardrailFunctionOutput(
        output_info={"reasons": reasons}, tripwire_triggered=bool(reasons)
    )


# ---------- 2) Output guardrail ----------
@output_guardrail
async def no_decision_guardrail(ctx, agent, output) -> GuardrailFunctionOutput:
    text = output if isinstance(output, str) else json.dumps(output, default=str)
    hits = [p for p in FORBIDDEN_OUTPUT if re.search(p, text, re.IGNORECASE)]
    return GuardrailFunctionOutput(
        output_info={"hits": hits}, tripwire_triggered=bool(hits)
    )


# ---------- 3) Tool guardrail (على create_claim_case) ----------
@tool_input_guardrail
def case_creation_guardrail(data) -> ToolGuardrailFunctionOutput:
    args = json.loads(data.context.tool_arguments or "{}")
    summary = args.get("summary", "")
    if any(re.search(p, summary, re.IGNORECASE) for p in FORBIDDEN_OUTPUT):
        return ToolGuardrailFunctionOutput.reject_content(
            "Blocked: the case summary contains an approval/denial/payment promise."
        )
    return ToolGuardrailFunctionOutput.allow()