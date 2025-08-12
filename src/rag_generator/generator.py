from typing import List
from transformers import GenerationConfig
from src.rag_generator.model_loader import load_model_and_tokenizer
from config.settings import MAX_TOKENS, REPLY_TEMPERATURE
from src.rag_generator.schemas import PatientGuideline
from src.guideline_retriever.schemas import RetrievedChunk
from src.condition_extractor.schemas import Condition
import re
import torch

SYSTEM_PROMPT = """You are a friendly Bangladeshi doctor.
Explain the condition in ≤ 200 words, using bullet points for Do's and Don'ts.
Speak in 6th-grade English. Include 1 simple reference line at the end.

Context:
{context}

Condition: {condition}
Answer:"""


class RAGGenerator:
    def __init__(self) -> None:
        self.model, self.tokenizer = load_model_and_tokenizer()

    def generate(
        self, conditions: List[Condition], chunks: List[RetrievedChunk]
    ) -> PatientGuideline:
        context = "\n".join(c.text for c in chunks)
        cond_names = ", ".join(c.name for c in conditions)

        prompt = f"Context:\n{context}\n\nCondition: {cond_names}\nAnswer:"
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        gen_config = GenerationConfig(
            max_new_tokens=MAX_TOKENS,
            temperature=REPLY_TEMPERATURE,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id,
        )

        with torch.no_grad():
            output_ids = self.model.generate(**inputs, generation_config=gen_config)
        reply = self.tokenizer.decode(
            output_ids[0][inputs["input_ids"].shape[-1] :],
            skip_special_tokens=True,
        )

        # Naïve bullet extraction (robust enough for smoke-test)
        dos = re.findall(r"- Do:\s*(.+)", reply, re.I)
        donts = re.findall(r"- Don't:\s*(.+)", reply, re.I)

        return PatientGuideline(
            summary=reply.split("\n")[0] if reply else "",
            dos=dos,
            donts=donts,
            references=[f"WHO {c.source_file}" for c in chunks],
        )
