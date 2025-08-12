import gradio as gr
import httpx

API_URL = "http://localhost:8000/guidelines"


def run_pipeline(medicines: str):
    meds = [m.strip() for m in medicines.split(",") if m.strip()]
    with httpx.Client() as client:
        # 1. match drugs
        r1 = client.post("http://localhost:8000/diagnose", json=meds)
        drugs = r1.json()["matched_drugs"]
        if not drugs:
            return "❌ No drug matches."
        # 2. build conditions list (naïve: first match per med)
        conds = [
            {
                "name": drugs[0]["indications"][:50],
                "icd10": None,
                "confidence": 0.9,
            }
        ]
        r2 = client.post(API_URL, json=conds)
        return r2.json()["markdown"]


iface = gr.Interface(
    fn=run_pipeline,
    inputs=gr.Textbox(label="Medicines (comma-separated)"),
    outputs=gr.Markdown(label="Patient-friendly Guideline"),
    title="RAG-Med Demo",
    examples=[["Metformin, Lisinopril"]],
)
if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=7860)
