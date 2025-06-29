import os
from langchain.schema import Document
from transformers import (
    pipeline,
    BitsAndBytesConfig,
    AutoModelForCausalLM,
    AutoTokenizer,
)
from langchain.chains.summarize import load_summarize_chain
from langchain_huggingface import HuggingFacePipeline
import torch
from dotenv import load_dotenv

load_dotenv()

WEEKLY_PRODUCTIVITY_JSONL = os.getenv("WEEKLY_PRODUCTIVITY_JSONL")
REPORT_ROOT_PATH = os.getenv("REPORT_ROOT_PATH")
LLM_SUMMARY_OUTPUT_PATH = os.getenv("LLM_SUMMARY_OUTPUT_PATH")
LLM_MODEL = os.getenv("LLM_MODEL")

# Load tokenizer and model with 4-bit quantization
tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

model = AutoModelForCausalLM.from_pretrained(
    LLM_MODEL, quantization_config=quantization_config, device_map="auto"
)

documents = []

# Load JSONL documents
jsonl_path = os.path.join(REPORT_ROOT_PATH, WEEKLY_PRODUCTIVITY_JSONL)
with open(jsonl_path, "r") as f:
    documents.extend(
        [Document(page_content=line.strip()) for line in f if line.strip()]
    )

# Load Markdown document
markdown_path = os.path.join(REPORT_ROOT_PATH, "weekly_productivity_events.md")
with open(markdown_path, "r") as f:
    md_text = f.read()
    documents.append(Document(page_content=md_text))

# Create the pipeline, set pad_token_id explicitly to suppress warnings
pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=300,
    temperature=0.7,
    do_sample=True,
    pad_token_id=tokenizer.eos_token_id,
)

llm = HuggingFacePipeline(pipeline=pipe)

# Create summarization chain with LangChain
chain = load_summarize_chain(llm, chain_type="map_reduce")

try:
    summary = chain.invoke(documents)
except Exception as e:
    print(f"Error during summarization: {e}")
    summary = f"Error generating summary {e}"

# Write the summary output
output_path = os.path.join(REPORT_ROOT_PATH, LLM_SUMMARY_OUTPUT_PATH)
with open(output_path, "w") as f:
    f.write(summary)

print("Summary of weekly productivity:")
print(summary)
