import re
from typing import List
from src.rag_generator.schemas import PatientGuideline


def to_markdown(guideline: PatientGuideline) -> str:
    """
    Convert PatientGuideline → plain-language markdown.
    Flesch-Kincaid ≈ 6th grade.
    """
    lines = [f"### 🏥 {guideline.summary}", ""]
    if guideline.dos:
        lines += ["**✅ Do:**"] + [f"- {d}" for d in guideline.dos] + [""]
    if guideline.donts:
        lines += ["**❌ Don’t:**"] + [f"- {d}" for d in guideline.donts] + [""]
    if guideline.references:
        lines += ["**📚 References:**"] + [f"- {r}" for r in guideline.references]
    return "\n".join(lines)


def split_bullets(text: str) -> tuple[List[str], List[str]]:
    """Utility for legacy string → dos/donts split."""
    dos = re.findall(r"- Do:\s*(.+)", text, re.I)
    donts = re.findall(r"- Don(?:’|')?t:\s*(.+)", text, re.I)
    return dos, donts
