import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)
from config.settings import LLM_MODEL_NAME, USE_4BIT_QUANT


def load_model_and_tokenizer():
    if USE_4BIT_QUANT:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
    else:
        bnb_config = None

    tokenizer = AutoTokenizer.from_pretrained(
        LLM_MODEL_NAME,
        padding_side="left",
    )
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        LLM_MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.float16,
    )
    return model, tokenizer
