"""
Quick test that the Groq API key works.
"""
import json
import os
import requests

# 1. Set API key and endpoint
api_key = os.getenv("GROQ_API_KEY") 
url = "https://api.groq.com/openai/v1/chat/completions"

# 2. Define headers required by the API
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

# 3. Build the payload
payload = {
    "model": "openai/gpt-oss-20b",
    "max_completion_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello! Write a haiku about code."}],
}

# 4. Send the POST request
response = requests.post(url, headers=headers, data=json.dumps(payload))

# 5. Parse and print the response
if response.status_code == 200:
    result = response.json()
    print(result["choices"][0]["message"]["content"])
else:
    print(f"Error {response.status_code}: {response.text}")
