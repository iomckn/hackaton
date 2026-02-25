import requests

def ollama_generate(prompt: str, model: str = "mistral") -> str:
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    r = requests.post(url, json=payload, timeout=60)
    r.raise_for_status()
    return r.json().get("response", "")