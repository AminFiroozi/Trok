import os
import google.generativeai as genai
from dotenv import load_dotenv

# --- 1. Define Your Context and Query ---

# This is where you'd put your large block of text.
# For this example, we'll use a moderately sized string.
# In a real application, you might load this from a file or a database.
# This entire `direct_context` string will be sent to the model.
# direct_context = """
# The Atacama Desert, located in northern Chile, is renowned as one of the driest places on Earth.
# Some areas within the desert have gone centuries without significant rainfall.
# Its unique geography, situated between the Andes Mountains to the east and the Chilean Coast Range
# to the west, creates a powerful rain shadow effect. Prevailing winds lose their moisture
# over these mountain ranges before reaching the Atacama.

# Despite its hyper-arid conditions, the Atacama Desert is not devoid of life.
# Various species of flora, such as hardy grasses, cacti, and shrubs, have adapted to survive
# with minimal water. Some plants, known as 'camanchaca fog oasis' flora, derive moisture
# directly from the coastal fog (camanchaca) that rolls in from the Pacific Ocean.
# The animal life includes insects, lizards, rodents, and even some species of foxes and birds
# that have adapted to the harsh environment.

# The Atacama is also a prime location for astronomical observation due to its high altitude,
# clear skies, and lack of light pollution. Several major international observatories,
# such as the Paranal Observatory (home to the Very Large Telescope) and ALMA (Atacama Large
# Millimeter/submillimeter Array), are located here. These facilities allow astronomers to
# study distant galaxies, star formation, and the early universe with unprecedented clarity.

# Furthermore, the desert's unique geology makes it rich in mineral resources, including copper
# (Chile is the world's largest copper producer), lithium, silver, and gold. Mining activities
# have a significant economic impact but also raise environmental concerns that require careful management.
# Historically, the region was also important for its sodium nitrate deposits, heavily exploited
# in the late 19th and early 20th centuries.
# """

# user_query = "What makes the Atacama Desert a good location for astronomical observatories, and what are some of its economic activities?"

# --- 2. Construct the Prompt ---
# We combine the context and the query into a single prompt.
# You can experiment with different ways to structure this.
# Common methods include:
# - "Context: [your context]\n\nQuestion: [your query]"
# - "Based on the following text:\n[your context]\n\nAnswer this: [your query]"
def get_LLM_response(direct_context, user_query):
    print("direct_context", direct_context)
    
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)

    prompt_with_direct_context = f"""Please read the following text carefully:

    --- BEGIN PROVIDED TEXT ---
    {direct_context}
    --- END PROVIDED TEXT ---
    
    In the answer don't mention any character like " or \\" or \\n or text 
    answer normally and not in the format of text: "<answer>\\n"
    And answer the following question with the information provided in the text above:
    Question: {user_query}

    """
    # prompt_with_direct_context = f"""Please read the following text carefully:

    # --- BEGIN PROVIDED TEXT ---
    # {direct_context}
    # --- END PROVIDED TEXT ---

    # Based *only* on the information provided in the text above, please answer the following question:
    # Question: {user_query}

    # If the answer cannot be found in the text, please state that clearly.
    # """

    # --- 3. Interact with Gemini Generative Model ---
    # We'll use Gemini 1.5 Flash, which has a large context window.
    generative_model_name = 'gemini-1.5-flash-latest'
    print(f"\nUsing Gemini generative model: {generative_model_name}")
    try:
        model = genai.GenerativeModel(generative_model_name)


        # Generate content
        # You can also use generate_content_async for asynchronous calls
        response = model.generate_content(prompt_with_direct_context)

        # --- 4. Print the Response ---
        print("\n--- Gemini's Response ---")
        if response.parts:
            print(response.text, type(response.text))
            return response.text
            # return str(response.parts).split("\"")[1][:-2]
        elif response.candidates and response.candidates[0].finish_reason != "SAFETY":
            # Handle cases where content might be in candidates
            if response.candidates[0].content and response.candidates[0].content.parts:
                print("".join(part.text for part in response.candidates[0].content.parts))
                # return "".join(part.text for part in response.candidates[0].content.parts)
        else:
            # Handle blocked responses or other issues
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                print(f"Response blocked due to: {response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason}")
            else:
                for candidate in response.candidates: # Iterate through candidates for safety feedback
                    if candidate.finish_reason == "SAFETY":
                        print(f"Response content filtered due to safety concerns: {candidate.safety_ratings}")
                        break # Stop after finding the first safety-related blockage
                else: # If no candidate was blocked for safety but parts are still empty
                    print("Gemini produced an empty response or the content was filtered for other reasons.")

    except Exception as e:
        print(f"\nAn error occurred during Gemini API interaction: {e}")

    # --- Example of how you might load context from a file ---
    # if __name__ == "__main__":
    # try:
    # with open("my_large_context_document.txt", "r", encoding="utf-8") as f:
    #         file_context = f.read()
    # # Now you can use file_context instead of the hardcoded direct_context
    #         print(f"\nSuccessfully loaded context from file ({len(file_context)} characters).")
    # # You would then proceed to build the prompt and call the API as above.
    # except FileNotFoundError:
    # print("\nNote: 'my_large_context_document.txt' not found. Skipping file load example.")
    # except Exception as e:
    # print(f"\nError loading context from file: {e}")