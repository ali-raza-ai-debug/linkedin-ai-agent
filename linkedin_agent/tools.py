from ddgs import DDGS
from google.genai import types
from writer import client, MODELS


# ---------- YOUR OWN TOOL ----------

def web_search(query: str) -> str:
    """Search the web and return the top results.

    Args:
        query: What to search for, e.g. "supervised learning real world examples 2026".
    """
    print(f"   🔎 Agent is searching: {query}")
    try:
        results = DDGS().text(query, max_results=5)
    except Exception as error:
        return f"Search failed: {error}"

    lines = []
    for result in results:
        lines.append(f"- {result['title']}: {result['body']} ({result['href']})")
    return "\n".join(lines) if lines else "No results found."


# ---------- THE RESEARCHER ----------

RESEARCH_PROMPT = """
You are a research assistant. Use the web_search tool (1-3 searches)
to find 3-5 short, accurate points about this topic that would make a
beginner-friendly LinkedIn post more interesting: real-world examples,
fresh facts, or recent news.

Topic: {topic}

Rules:
- Keep each point to 1-2 sentences
- Only include facts you found in the search results
- Add the source name in brackets after each point
"""


def research_topic(topic):
    """Let Gemini use our web_search tool to collect notes."""
    config = types.GenerateContentConfig(
        tools=[web_search],
        temperature=0.3,
    )
    prompt = RESEARCH_PROMPT.format(topic=topic)

    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model, contents=prompt, config=config
            )
            return response.text
        except Exception as error:
            print(f"   ({model} failed: {str(error)[:40]})")

    print("   ⚠️ Research failed. Writing the post without it.")
    return ""


# ---------- TEST: run this file directly to try the tool ----------

if __name__ == "__main__":
    query = input("Search for: ")
    print(web_search(query))