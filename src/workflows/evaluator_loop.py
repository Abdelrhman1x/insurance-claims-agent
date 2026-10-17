import re

from agents import Runner

from src.agents.writer import evaluator_agent, writer_agent

MAX_ATTEMPTS = 3

# فحص بايثون (مش LLM): عبارات ممنوعة في الملخص
FORBIDDEN = [
    r"claim (is|has been|was) (approved|rejected|denied)",
    r"(we|the company|insurer) (will|shall) (pay|compensate|reimburse)",
    r"\bguarantee[sd]?\b",
    r"\byou will (be paid|receive|get)\b",
    r"\bapproved for payment\b",
]


def python_check(summary: str) -> list[str]:
    return [
        f"Forbidden phrase matched: {p}"
        for p in FORBIDDEN
        if re.search(p, summary, re.IGNORECASE)
    ]


def parse_review(text: str) -> tuple[bool, list[str]]:
    text = (text or "").strip()
    if text.upper().startswith("APPROVED"):
        return True, []
    issues = text.split(":", 1)[-1].split(";")
    return False, [i.strip() for i in issues if i.strip()] or ["Unspecified issue"]


async def write_with_review(context: str) -> dict:
    feedback, summary, history = "", "", []

    for attempt in range(1, MAX_ATTEMPTS + 1):
        prompt = context if not feedback else (
            f"{context}\n\nPREVIOUS DRAFT:\n{summary}\n\n"
            f"REVIEWER FEEDBACK (fix all):\n{feedback}"
        )
        summary = (await Runner.run(writer_agent, prompt)).final_output

        issues = python_check(summary)  # أولًا: فحص الكود
        if not issues:                  # لو نضيف: نسأل الـ Evaluator
            raw = (await Runner.run(
                evaluator_agent, f"EVIDENCE:\n{context}\n\nSUMMARY:\n{summary}"
            )).final_output
            approved, issues = parse_review(raw)
        else:
            approved = False

        history.append({"attempt": attempt, "approved": approved, "issues": issues})
        print(f"[attempt {attempt}] approved={approved} issues={issues}")

        if approved:
            return {"summary": summary, "approved": True, "attempts": attempt, "history": history}
        feedback = "\n".join(f"- {i}" for i in issues)

    return {"summary": summary, "approved": False, "attempts": MAX_ATTEMPTS, "history": history}