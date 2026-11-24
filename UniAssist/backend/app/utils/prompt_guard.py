"""Prompt-injection safeguards.

Uploaded documents are UNTRUSTED data. Two layers:
1. Heuristic scan at ingestion flags chunks that look like instructions to the model.
2. At answer time (Phase 4) retrieved text is wrapped in delimiters and the system prompt
   states that anything inside them is data, never instructions.
Heuristics are a signal, not a guarantee; layer 2 is the primary defence.
"""
import re

PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above) (instructions|prompts?)",
    r"disregard (all |any |the )?(previous|prior|above|system)",
    r"you are now\b", r"act as (an? )?(?!student)", r"system prompt",
    r"reveal (your|the) (instructions|prompt|api key)", r"developer mode",
    r"new instructions\s*:", r"do not (follow|obey) (the )?(system|previous)",
]
_RX = [re.compile(p, re.I) for p in PATTERNS]


def looks_like_injection(text: str) -> bool:
    return any(rx.search(text) for rx in _RX)


def wrap_untrusted(chunks):
    """Format retrieved chunks as clearly delimited, untrusted context."""
    parts = []
    for i, c in enumerate(chunks, 1):
        body = c["text"].replace("<<<", "").replace(">>>", "")
        parts.append(f"<<<SOURCE {i} | {c['filename']} | page {c['page']}>>>\n{body}\n<<<END SOURCE {i}>>>")
    return "\n\n".join(parts)
