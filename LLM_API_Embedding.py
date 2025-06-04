import google.generativeai as genai
import numpy as np
from dotenv import load_dotenv
import faiss
import os
load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

# Configure the Gemini API with the API key
genai.configure(api_key=GOOGLE_API_KEY)

# --- 1. Prepare Your Knowledge Base ---
documents = [
    "The Atacama Desert in Chile is one of the driest places on Earth.",
    "Some weather stations in the Atacama have never recorded rainfall.",
    "Despite its aridity, over 500 species of vascular plants have adapted to life in the Atacama.",
    "The Gemini models are a family of multimodal AI models developed by Google DeepMind.",
    "Gemini can understand and generate text, code, images, and is designed for complex reasoning tasks.",
    "The Gemini API provides access to models like 'gemini-1.5-flash' for generation and 'models/embedding-001' for text embeddings.",
    "Solar eclipses occur when the Moon passes between the Sun and Earth, casting a shadow on Earth."
]
text_chunks = documents # Using full documents as chunks for simplicity

# --- 2. Initialize Gemini Embedding Model ---
# You'll use 'models/embedding-001' or the latest recommended embedding model.
EMBEDDING_MODEL_NAME = 'models/embedding-001'

print(f"Using Gemini embedding model: {EMBEDDING_MODEL_NAME}")

def get_gemini_embeddings(texts_to_embed):
    """Helper function to get embeddings from Gemini API."""
    if isinstance(texts_to_embed, str):
        texts_to_embed = [texts_to_embed]

    try:
        result = genai.embed_content(
            model=EMBEDDING_MODEL_NAME,
            content=texts_to_embed,
            task_type="RETRIEVAL_DOCUMENT"
        )
        return np.array(result['embedding']) if isinstance(texts_to_embed, str) else [np.array(e) for e in result['embedding']]
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        # Return empty numpy array for single text, or list of empty arrays for multiple texts
        if isinstance(texts_to_embed, str):
            return np.array([])
        return [np.array([]) for _ in texts_to_embed]


# --- 3. Generate Embeddings for Your Knowledge Base ---
print("Generating embeddings for documents using Gemini API...")
document_embeddings_list = []
for chunk in text_chunks:
    embedding = get_gemini_embeddings(chunk)
    if isinstance(embedding, np.ndarray) and embedding.size > 0:  # Check if embedding was successful
        document_embeddings_list.append(embedding)
    else:
        print(f"Warning: Could not generate embedding for chunk: '{chunk[:50]}...'")

if not document_embeddings_list:
    print("No document embeddings were generated. Exiting.")
    exit()

document_embeddings = np.array(document_embeddings_list).astype('float32')

if document_embeddings.ndim == 1 and document_embeddings.size == 0: # Single failed embedding
     print("Failed to generate any document embeddings. Exiting.")
     exit()
elif document_embeddings.ndim > 1 and document_embeddings.shape[0] == 0 : # Multiple failed embeddings resulting in empty array
     print("Failed to generate any document embeddings. Exiting.")
     exit()


# --- 4. Create and Populate a Vector Store (using FAISS) ---
embedding_dimension = document_embeddings.shape[1]
print(f"Creating FAISS index with dimension {embedding_dimension}...")
index = faiss.IndexFlatL2(embedding_dimension)
index.add(document_embeddings)
print(f"Added {index.ntotal} embeddings to the FAISS index.")

# --- 5. Process User Query and Retrieve Context ---
def get_relevant_context_from_gemini_embeddings(query, top_k=2):
    print(f"\nUser Query: '{query}'")
    try:
        query_embedding_result = genai.embed_content(
            model=EMBEDDING_MODEL_NAME,
            content=query,
            task_type="RETRIEVAL_QUERY"
        )
        query_embedding = np.array([query_embedding_result['embedding']]).astype('float32')
    except Exception as e:
        print(f"Error generating query embedding: {e}")
        return []


    if query_embedding.size == 0:
        print("Could not generate embedding for the query.")
        return []

    print("Searching for relevant documents in FAISS index...")
    distances, indices = index.search(query_embedding, top_k)

    retrieved_chunks = [text_chunks[i] for i in indices[0] if i < len(text_chunks)]

    print("Retrieved Context:")
    for i, chunk in enumerate(retrieved_chunks):
        print(f"  {i+1}. {chunk} (Distance: {distances[0][i]:.4f})")
    return retrieved_chunks

# --- 6. Construct the Prompt for Gemini ---
def construct_gemini_prompt(query, retrieved_context):
    if not retrieved_context:
        # Fallback if no context is retrieved
        prompt = f"Please answer the following question: {query}\n\nNote: I could not find specific context in my knowledge base for this query."
    else:
        context_str = "\n\n".join(retrieved_context)
        prompt = f"""Based on the following context:
---
{context_str}
---
Please answer the following question: {query}
If the context doesn't provide enough information to answer the question directly, indicate that.
"""
    return prompt

# --- 7. Interact with Gemini Generative Model ---
GENERATIVE_MODEL_NAME = 'gemini-1.5-flash-latest' # Or 'gemini-1.0-pro', 'gemini-1.5-pro-latest' etc.
print(f"\nUsing Gemini generative model: {GENERATIVE_MODEL_NAME}")
generative_model = genai.GenerativeModel(GENERATIVE_MODEL_NAME)

def get_gemini_response(prompt_with_context):
    print("\n--- Augmented Prompt for Gemini ---")
    print(prompt_with_context)
    print("--- End of Gemini Prompt ---\n")
    try:
        response = generative_model.generate_content(prompt_with_context)
        # Depending on the model and safety settings, you might need to check response.candidates
        # and response.prompt_feedback
        if response.candidates:
             # For simple text, usually the first candidate is sufficient
             if response.candidates[0].content.parts:
                return response.candidates[0].content.parts[0].text
             else: # Handle cases where there are no parts (e.g. finish reason BLOCK)
                return f"Gemini finished with reason: {response.candidates[0].finish_reason}. No text parts."
        else: # No candidates, possibly due to safety ratings or other issues
            return f"Gemini returned no candidates. Prompt feedback: {response.prompt_feedback}"

    except Exception as e:
        print(f"Error during Gemini generation: {e}")
        return "Error: Could not get response from Gemini."

# --- Example Usage ---
if __name__ == "__main__":
    user_query = "What is Gemini known for?"
    retrieved_context_for_query = get_relevant_context_from_gemini_embeddings(user_query, top_k=2)
    augmented_prompt = construct_gemini_prompt(user_query, retrieved_context_for_query)
    gemini_answer = get_gemini_response(augmented_prompt)
    print(f"Gemini's Answer:\n{gemini_answer}\n")

    print("-" * 50)

    user_query_2 = "Tell me about dry places."
    retrieved_context_for_query_2 = get_relevant_context_from_gemini_embeddings(user_query_2, top_k=1)
    augmented_prompt_2 = construct_gemini_prompt(user_query_2, retrieved_context_for_query_2)
    gemini_answer_2 = get_gemini_response(augmented_prompt_2)
    print(f"Gemini's Answer:\n{gemini_answer_2}\n")

    print("-" * 50)

    user_query_3 = "When do solar eclipses happen?" # This is in our context
    retrieved_context_for_query_3 = get_relevant_context_from_gemini_embeddings(user_query_3, top_k=1)
    augmented_prompt_3 = construct_gemini_prompt(user_query_3, retrieved_context_for_query_3)
    gemini_answer_3 = get_gemini_response(augmented_prompt_3)
    print(f"Gemini's Answer:\n{gemini_answer_3}\n")