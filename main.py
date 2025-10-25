import requests
import json
import warnings

# Suppress LibreSSL warnings
warnings.filterwarnings("ignore")

# Hard-coded endpoint + API key
URL = "https://janitorai.com/hackathon/completions"
API_KEY = "calhacks2047"

# Hard-coded payload
payload = {
    "model": "ignored",  # this field is ignored by JanitorAI
    "messages": [
        {"role": "system", "content": "You are a friendly game-master."},
        {"role": "user", "content": "Start a scene in a crowded spaceship bar."}
    ],
    "max_tokens": 1000
}

# Hard-coded headers
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Make request
response = requests.post(URL, headers=headers, data=json.dumps(payload))

# Display result cleanly
print("Status code:", response.status_code)

try:
    data = response.json()
    message = data["choices"][0]["message"].get("content", "")
    print("\nAssistant reply:\n", message)
except Exception as e:
    print("Raw response:\n", response.text)
    print("\nError parsing JSON:", e)