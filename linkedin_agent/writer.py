import os
import time
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv(override=True)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Models to try, in order. If one is busy, try the next.
MODELS = MODELS = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest", "gemini-3.5-flash-lite"]

# ---------- PROMPTS ----------

WRITER_PROMPT = """
You are a LinkedIn ghostwriter for Ali, an AI/ML learner from Pakistan
who studied at the University of Lahore. He knows Python, Machine Learning
and Deep Learning, and is now learning LLMs and AI agents in public.

Write LinkedIn posts with these rules:
- Start with a strong hook in the first line (short and curious)
- Use short lines and blank lines between them (easy to read on mobile)
- Explain ideas simply, like teaching a beginner
- Use a few emojis, but not too many
- Write in first person, as Ali, friendly and humble
- End with a question to the audience
- Add 4-6 relevant hashtags at the end
- Keep it under 1300 characters
- Never invent fake achievements, jobs or numbers
- Never use markdown like **bold** or # headings (LinkedIn shows them as plain symbols)
- Don't invent personal stories or memories; only describe Ali's learning in general terms

"""

CRITIC_PROMPT = """
You are a strict LinkedIn content editor.
Grade the post from 1 to 10 based on:
- Hook: does the first line make people stop scrolling?
- Clarity: can a beginner understand it?
- Readability: short lines, easy on mobile?
- Honesty: no fake claims or made-up numbers?
- Ending: does it end with a good question and hashtags?
- Formatting: any markdown symbols like ** or #? (lower the score if yes)
Give short, specific feedback on what to improve.
"""

# ---------- DATA SHAPE FOR THE CRITIC ----------

class Review(BaseModel):
    score: int
    feedback: str

# ---------- HELPER: talk to Gemini ----------

def ask_gemini(prompt, system, temperature=0.7, schema=None, attempts=3):
    """Send a prompt to Gemini. Try backup models, and wait + retry if all are busy."""
    config = types.GenerateContentConfig(
        system_instruction=system,
        temperature=temperature,
        response_mime_type="application/json" if schema else None,
        response_schema=schema,
    )
    for attempt in range(1, attempts + 1):
        for model in MODELS:
            try:
                response = client.models.generate_content(
                    model=model, contents=prompt, config=config
                )
                return response.parsed if schema else response.text
            except Exception as error:
                print(f"   ({model} failed: {str(error)[:40]})")

        if attempt < attempts:
            print(f"   ⏳ All models busy. Waiting 20 seconds... (attempt {attempt}/{attempts})")
            time.sleep(20)

    raise RuntimeError("All models are busy. Try again in a few minutes.")
    
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model, contents=prompt, config=config
            )
            return response.parsed if schema else response.text
        except Exception as error:
            print(f"   ({model} failed: {str(error)[:60]})")
    raise RuntimeError("All models are busy. Try again in a few minutes.")

# ---------- THE AGENT'S SKILLS ----------
def write_post(topic, style, research=""):
    prompt = f"Write a LinkedIn post.\nTopic: {topic}\nStyle: {style}"
    if research:
        prompt += (
            f"\n\nResearch notes (use 1-2 of these facts to make the post fresh):\n"
            f"{research}\n\n"
            f"Only use facts from these notes. Don't invent statistics."
        )
    return ask_gemini(prompt, WRITER_PROMPT, temperature=0.9)

def review_post(post):
    prompt = f"Grade this LinkedIn post:\n\n{post}"
    return ask_gemini(prompt, CRITIC_PROMPT, temperature=0.2, schema=Review)

def improve_post(post, feedback):
    prompt = (
        f"Improve this LinkedIn post using the feedback.\n\n"
        f"POST:\n{post}\n\nFEEDBACK:\n{feedback}\n\n"
        f"Return only the improved post."
    )
    return ask_gemini(prompt, WRITER_PROMPT, temperature=0.7)

def save_post(post):
    folder = os.path.join(os.path.dirname(__file__), "posts")
    os.makedirs(folder, exist_ok=True)
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M") + ".txt"
    path = os.path.join(folder, filename)
    with open(path, "w", encoding="utf-8") as file:
        file.write(post)
    return path

# ---------- THE AGENT'S WORKFLOW ----------
def create_post(topic, style, research="", min_score=8, max_rounds=2):
    print("✍️  Writing first draft...")
    post = write_post(topic, style, research)
    score = 0

    for round_number in range(1, max_rounds + 1):
        print(f"\n🧑‍⚖️  Reviewing (round {round_number})...")
        review = review_post(post)
        score = review.score
        print(f"   Score: {score}/10")
        print(f"   Feedback: {review.feedback}")

        if score >= min_score:
            print("\n✅ Good enough!")
            break

        if round_number < max_rounds:
            print("\n🔁 Improving the post...")
            post = improve_post(post, review.feedback)

    return post, score

# ---------- RUN ----------

if __name__ == "__main__":
    topic = input("Topic: ")
    style = input("Style (explainer / lesson / mistake / build / question): ")
    print()

    final_post, score = create_post(topic, style)
    path = save_post(final_post)

    print("\n" + "=" * 50)
    print(final_post)
    print("=" * 50)
    print(f"\n💾 Saved to: {path}")