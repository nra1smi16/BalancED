"""
Quick test that your API key works, written the same way as the professor's example.
Run it from the project folder:   python ai_test.py

Needs:  pip install requests
Key:    PowerShell:  $env:ANTHROPIC_API_KEY = "your-key"     (never paste the key into this file)

Three lines differ from the example, because the original would not work:
  - url:    the API address is https://api.anthropic.com/v1/messages (anthropic.com is just a website)
  - model:  an older model name was used; this uses claude-haiku-5-5
  - status: the success code is 200 (the example also accepted 250, which the API never returns)
"""
import json
import os
import requests

# 1. Set your API key and endpoint
api_key = os.getenv("ANTHROPIC_API_KEY")  # Or paste your key directly
url = "https://api.anthropic.com/v1/messages"

# 2. Define headers required by Anthropic API
headers = {
    "x-api-key": api_key,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}

# 3. Build the payload
payload = {
    "model": "claude-haiku-5-5",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello, Claude! Write a haiku about code."}],
}

# 4. Send the POST request
response = requests.post(url, headers=headers, data=json.dumps(payload))

# 5. Parse and print the response
if response.status_code == 200:
    result = response.json()
    # keep only the text blocks (the reply can also contain other kinds of blocks)
    print("".join(block["text"] for block in result["content"] if block["type"] == "text"))
else:
    print(f"Error {response.status_code}: {response.text}")
