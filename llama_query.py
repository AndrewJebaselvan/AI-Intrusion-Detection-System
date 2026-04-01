from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from networkx import nodes
from transformers import pipeline

# ---------------- EMBEDDING MODEL (LOCAL) ----------------
embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# ---------------- LOAD LOG FILE ----------------
documents = SimpleDirectoryReader(
    input_files=["events.log"]
).load_data()

# ---------------- CREATE INDEX ----------------
index = VectorStoreIndex.from_documents(
    documents,
    embed_model=embed_model
)

# ---------------- RETRIEVER (NO LLM HERE) ----------------
retriever = index.as_retriever()

# ---------------- LOCAL LLM (COMPATIBLE MODEL) ----------------
llm = pipeline(
    "text-generation",
    model="distilgpt2",
    max_new_tokens=120,
    truncation=True
)

# ---------------- MAIN FUNCTION ----------------
def ask_question(query):
    nodes = retriever.retrieve(query)

    # Extract context safely
    context = "\n".join([node.text for node in nodes])[:800]

    # 🔥 RULE-BASED LOGIC (VERY IMPORTANT)
    if "intrusion" in query.lower():
        if "HIGH" in context:
            return "High-level intrusion detected. Multiple frames show a person inside a restricted zone with high threat scores."
        elif "MEDIUM" in context:
            return "Medium-level intrusion detected."
        else:
            return "No significant intrusion detected."

    # 🔥 FALLBACK AI
    prompt = f"""
Context:
{context}

Question: {query}

Answer in one clear sentence:
"""

    response = llm(prompt)[0]["generated_text"]

    # Clean output
    return response.split("Answer:")[-1].strip()