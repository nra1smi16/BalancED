"""
Quick test that your Groq API key works, written the same way as the professor's example.
Run it from the project folder:   python ai_test.py

Needs:  pip install requests
Key:    PowerShell:  $env:GROQ_API_KEY = "your-key"     (never paste the key into this file)
Get a free key at https://console.groq.com

The steps are the same as in the professor's example. What changes for Groq:
  - url:     https://api.groq.com/openai/v1/chat/completions
  - headers: the key goes in "Authorization: Bearer <key>"
  - payload: the same "messages" list, plus the model name
  - reply:   the text is in result["choices"][0]["message"]["content"]
"""
import json
import os
import requests

# 1. Set your API key and endpoint
api_key = os.getenv("GROQ_API_KEY")  # Or paste your key directly
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
