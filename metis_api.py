import requests
import json
import os
from dotenv import load_dotenv
import argparse

# Load environment variables from .env file
load_dotenv()

def process_with_ai(api_key, user_input):
    url = "https://api.metisai.ir/api/v1/completions"
    
    headers = {
        "authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": user_input,
        "max_tokens": 1000,
        "temperature": 0.7,
        "model": "text-davinci-003"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()
        
        # Print response for debugging
        print("Debug - Response:", json.dumps(response_data, indent=2))
        
        # Extract the AI's response
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['text'].strip()
        elif 'text' in response_data:
            return response_data['text'].strip()
        return None
            
    except Exception as e:
        print(f"Error: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response.text}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Process text with AI')
    parser.add_argument('--input', '-i', help='Input text to process')
    args = parser.parse_args()

    API_KEY = os.getenv('METIS_API_KEY')
    
    if not API_KEY:
        print("Error: METIS_API_KEY environment variable is not set")
        exit(1)

    user_input = args.input
    if not user_input:
        user_input = input("Enter your text to process: ")

    result = process_with_ai(API_KEY, user_input)
    
    if result:
        print("\nAI Response:")
        print(result)
    else:
        print("Failed to get response from AI")

if __name__ == "__main__":
    main() 