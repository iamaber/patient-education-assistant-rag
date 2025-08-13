import gradio as gr
import httpx
from src.condition_extractor.schemas import Condition
from src.rag_generator.schemas import PatientGuideline
from src.guideline_formatter.formatter import to_markdown

DIAGNOSE_URL = "http://localhost:8000/diagnose"
GUIDELINES_URL = "http://localhost:8000/guidelines"
HTTP_TIMEOUT = 30


def run_pipeline(medicines: str) -> str:
    """End-to-end pipeline: medicines → conditions → guidelines → markdown"""
    meds = [m.strip() for m in medicines.split(",") if m.strip()]
    if not meds:
        return "❌ No medicines provided."

    with httpx.Client(timeout=HTTP_TIMEOUT) as client:
        # 1. Drug matching
        r1 = client.post(DIAGNOSE_URL, json=meds)
        r1.raise_for_status()
        drugs = r1.json().get("matched_drugs", [])
        if not drugs:
            return "❌ No drug matches found."

        # 2. Build condition list with exact Pydantic schema
        conditions = []
        for d in drugs:
            drug = d.get("matched_drug", {})
            indications = drug.get("indications")
            if indications:
                conditions.append(
                    Condition(
                        name=indications[:60].strip(),
                        icd10=None,
                        confidence=d.get("confidence", 0.9),
                    ).dict()
                )

        if not conditions:
            return "❌ No indications extracted."

        # 3. Generate & format guideline
        r2 = client.post(GUIDELINES_URL, json=conditions)
        r2.raise_for_status()
        guideline = PatientGuideline(**r2.json()["guideline"])
        return to_markdown(guideline)


iface = gr.Interface(
    fn=run_pipeline,
    inputs=gr.Textbox(
        label="Medicines (comma-separated)",
        placeholder="e.g. Metformin, Lisinopril",
    ),
    outputs=gr.Markdown(label="Patient-friendly Guideline"),
    title="RAG-Med Assistant",
    examples=[["Metformin, Lisinopril"]],
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=7860, share=False)
