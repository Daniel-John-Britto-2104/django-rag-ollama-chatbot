import requests

try:
    response = requests.get("http://localhost:11434/api/tags")
    if response.status_code == 200:
        models = response.json().get("models", [])
        print("Available Ollama Models:")
        for model in models:
            print(" -", model.get("name"))
    else:
        print("Failed to reach Ollama server.")
except Exception as e:
    print(f"Error connecting to Ollama: {e}")