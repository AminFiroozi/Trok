import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# --- 1. Prepare Your Knowledge Base ---
# Let's say these are your documents (your context)
documents = [
    "The Eiffel Tower, located in Paris, France, was completed in 1889.",
    "It was designed and built by Gustave Eiffel's company.",
    "The tower is 330 meters tall and was the tallest man-made structure in the world until 1930.",
    "Millions of people visit the Eiffel Tower every year.",
    "Llama 3 is a large language model developed by Meta AI.",
    "It comes in various sizes, including 8B and 70B parameter versions.",
    "Llama 3 was trained on a massive dataset of text and code.",
    "Artificial intelligence is rapidly evolving, with new models appearing frequently."
]

# For simplicity, we'll treat each document as a single "chunk".
# In a real application, you'd likely split larger documents into smaller, meaningful chunks.
text_chunks = documents

# --- 2. Initialize Embedding Model ---
# You can choose from many models: https://www.sbert.net/docs/pretrained_models.html
# 'all-MiniLM-L6-v2' is a good starting point for its balance of speed and quality.
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# --- 3. Generate Embeddings for Your Knowledge Base ---
print("Generating embeddings for documents...")
document_embeddings = embedding_model.encode(text_chunks, convert_to_tensor=False)
# Ensure embeddings are float32, which FAISS expects
document_embeddings = np.array(document_embeddings).astype('float32')

# --- 4. Create and Populate a Vector Store (using FAISS) ---
embedding_dimension = document_embeddings.shape[1]  # Get the dimension of the embeddings

# Build a FAISS index
# IndexFlatL2 is a simple L2 distance (Euclidean) index
print(f"Creating FAISS index with dimension {embedding_dimension}...")
index = faiss.IndexFlatL2(embedding_dimension)

# Add the document embeddings to the index
index.add(document_embeddings)
print(f"Added {index.ntotal} embeddings to the FAISS index.")

# --- 5. Process User Query and Retrieve Context ---
def get_relevant_context(query, top_k=3):
    print(f"\nUser Query: '{query}'")
    # Embed the user's query
    query_embedding = embedding_model.encode([query], convert_to_tensor=False)
    query_embedding = np.array(query_embedding).astype('float32')

    # Search the FAISS index for similar document embeddings
    # D will contain distances, I will contain the indices of the similar documents
    print("Searching for relevant documents in FAISS index...")
    distances, indices = index.search(query_embedding, top_k)

    # Retrieve the actual text chunks
    retrieved_chunks = [text_chunks[i] for i in indices[0]] # indices[0] because query_embedding was a batch of 1

    print("Retrieved Context:")
    for i, chunk in enumerate(retrieved_chunks):
        print(f"  {i+1}. {chunk} (Distance: {distances[0][i]:.4f})")
    return retrieved_chunks

# --- 6. Construct the Prompt for Llama 3 ---
def construct_prompt(query, retrieved_context):
    context_str = "\n\n".join(retrieved_context)
    prompt = f"""Based on the following context:
---
{context_str}
---
Please answer the following question: {query}
If the context doesn't provide enough information, say so.
"""
    return prompt

# --- 7. Interact with Llama 3 (Conceptual) ---
# This is where you would call your Llama 3 model.
# The implementation depends on how you're running Llama 3:
# - Hugging Face Transformers library
# - A local server like Ollama (e.g., using `requests` library)
# - llama.cpp via its Python bindings
# - A cloud API

def get_llama3_response(prompt_with_context):
    print("\n--- Augmented Prompt for Llama 3 ---")
    print(prompt_with_context)
    print("--- End of Llama 3 Prompt ---\n")

    # **Replace this with your actual Llama 3 model call**
    # Example (conceptual - this won't run without a Llama 3 setup):
    #
    # from transformers import pipeline
    # llama_pipeline = pipeline("text-generation", model="meta-llama/Llama-2-7b-chat-hf" or your_llama3_model_path) # Replace with actual Llama 3 model
    # response = llama_pipeline(prompt_with_context, max_new_tokens=150)
    # return response[0]['generated_text']
    #
    # Or using Ollama (if Ollama server is running with Llama 3):
    # import requests
    # import json
    # try:
    #     ollama_response = requests.post('http://localhost:11434/api/generate',
    #                                     json={
    #                                         "model": "llama3", # Or your specific Llama 3 model name in Ollama
    #                                         "prompt": prompt_with_context,
    #                                         "stream": False
    #                                     })
    #     ollama_response.raise_for_status()
    #     return json.loads(ollama_response.text).get("response")
    # except Exception as e:
    #     print(f"Error contacting Ollama or processing response: {e}")
    #     return "Error: Could not get response from Llama 3. (Conceptual)"

    return f"Llama 3 would process this prompt and generate an answer. (Query: '{user_query}')"


# --- Example Usage ---
if __name__ == "__main__":
    user_query = "What is the Eiffel Tower?"
    retrieved_context = get_relevant_context(user_query, top_k=3)
    augmented_prompt = construct_prompt(user_query, retrieved_context)
    llama3_answer = get_llama3_response(augmented_prompt)
    print(f"Llama 3's (Conceptual) Answer:\n{llama3_answer}\n")

    print("-" * 50)

    user_query_2 = "Tell me about Llama 3."
    retrieved_context_2 = get_relevant_context(user_query_2, top_k=2)
    augmented_prompt_2 = construct_prompt(user_query_2, retrieved_context_2)
    llama3_answer_2 = get_llama3_response(augmented_prompt_2)
    print(f"Llama 3's (Conceptual) Answer:\n{llama3_answer_2}\n")

    print("-" * 50)

    user_query_3 = "What is the capital of Japan?" # This is not in our context
    retrieved_context_3 = get_relevant_context(user_query_3, top_k=2)
    augmented_prompt_3 = construct_prompt(user_query_3, retrieved_context_3)
    llama3_answer_3 = get_llama3_response(augmented_prompt_3)
    print(f"Llama 3's (Conceptual) Answer:\n{llama3_answer_3}\n")