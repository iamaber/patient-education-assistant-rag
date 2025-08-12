import gradio as gr
import httpx

from src.guideline_formatter.formatter import to_markdown
from src.rag_generator.schemas import PatientGuideline
from src.condition_extractor.schemas import Condition

API_URL = "http://localhost:8000/guidelines"
DIAGNOSE_URL = "http://localhost:8000/diagnose"


def run_pipeline(medicines: str):
    meds = [m.strip() for m in medicines.split(",") if m.strip()]
    if not meds:
        return "❌ No medicines provided."

    with httpx.Client(timeout=30) as client:
        # 1. Drug matching
        r1 = client.post(DIAGNOSE_URL, json=meds)
        r1.raise_for_status()
        drugs = r1.json().get("matched_drugs", [])
        if not drugs:
            return "❌ No drug matches found."

        # 2. Build condition list
        conditions = [
            Condition(
                name=d.get("matched_drug", {}).get("indications", "")[:60].strip(),
                icd10=None,
                confidence=d.get("confidence", 0.9),
            ).dict()
            for d in drugs
            if d.get("matched_drug", {}).get("indications")
        ]
        if not conditions:
            return "❌ No indications extracted."

        # 3. Generate guideline
        r2 = client.post(API_URL, json=conditions)
        r2.raise_for_status()
        guideline_data = r2.json()["guideline"]
        guideline = PatientGuideline(**guideline_data)
        return to_markdown(guideline)


iface = gr.Interface(
    fn=run_pipeline,
    inputs=gr.Textbox(label="Medicines (comma-separated)"),
    outputs=gr.Markdown(label="Patient-friendly Guideline"),
    title="RAG-Med Demo",
    examples=[["Metformin, Lisinopril"]],
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=7860, share=False)
