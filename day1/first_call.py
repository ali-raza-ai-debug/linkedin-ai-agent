from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client()

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Explain what a token is in LLMs in 2 lines."
)
print(response.text)