from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline

app = FastAPI()

# Load model once when the service starts
print("Loading model checkpoint shards...")
model_pipeline = pipeline("text-generation", model="gpt2")  # Replace with your model
print("Model loaded and ready.")


# Define request schema
class RequestInput(BaseModel):
    prompt: str
    max_length: int = 50


@app.post("/generate")
def generate_text(input: RequestInput):
    # Run inference without reloading the model
    outputs = model_pipeline(
        input.prompt, max_length=input.max_length, num_return_sequences=1
    )
    return {"generated_text": outputs[0]["generated_text"]}
