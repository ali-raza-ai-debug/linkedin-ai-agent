import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)
TOKEN = TOKEN = (os.getenv("LINKEDIN_ACCESS_TOKEN") or "").strip()
API = "https://api.linkedin.com"


def get_person_urn():
    """Ask LinkedIn who you are, and build your ID (URN)."""
    response = requests.get(
        API + "/v2/userinfo",
        headers={"Authorization": f"Bearer {TOKEN}"},
        timeout=30,
    )
    response.raise_for_status()
    return f"urn:li:person:{response.json()['sub']}"


def clean_text(text):
    """Add a backslash before symbols LinkedIn treats as special."""
    for symbol in ["\\", "(", ")", "[", "]", "{", "}", "<", ">", "@", "|", "*", "_", "~"]:
        text = text.replace(symbol, "\\" + symbol)
    return text


def post_to_linkedin(text):
    """Publish a text post on your LinkedIn profile."""
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "LinkedIn-Version": "202608",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }
    body = {
        "author": get_person_urn(),
        "commentary": clean_text(text),
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    response = requests.post(API + "/rest/posts", headers=headers, json=body, timeout=30)

    if response.status_code == 201:
        post_id = response.headers.get("x-restli-id")
        return f"https://www.linkedin.com/feed/update/{post_id}/"
    raise RuntimeError(f"LinkedIn error {response.status_code}: {response.text[:200]}")


if __name__ == "__main__":
    if not TOKEN:
        print("❌ LINKEDIN_ACCESS_TOKEN not found in .env")
    else:
        print("Your LinkedIn ID:", get_person_urn())
        message = input("Type a short TEST post (or press Enter to skip): ")
        if message:
            print("✅ Posted:", post_to_linkedin(message))