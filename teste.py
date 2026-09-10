import os
from dotenv import load_dotenv
from google import genai

# Carrega sua chave
load_dotenv()
chave = os.getenv("GEMINI_API_KEY")

# Conecta direto no Google, ignorando o CrewAI por enquanto
client = genai.Client(api_key=chave)

print("🔍 Buscando modelos disponíveis na sua chave...\n")
for modelo in client.models.list():
    if "generateContent" in modelo.supported_generation_methods:
        print(f"- {modelo.name}")