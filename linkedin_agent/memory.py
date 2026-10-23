import json
import os
from datetime import date

TOPICS_FILE = os.path.join(os.path.dirname(__file__), "topics.json")


def load_topics():
    """Read the content plan from topics.json."""
    with open(TOPICS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_topics(topics):
    """Write the updated content plan back to topics.json."""
    with open(TOPICS_FILE, "w", encoding="utf-8") as file:
        json.dump(topics, file, indent=2, ensure_ascii=False)


def get_next_topic():
    """Return the first topic that hasn't been posted yet."""
    for topic in load_topics():
        if not topic["posted"]:
            return topic
    return None


def mark_posted(topic_id):
    """Mark a topic as posted, with today's date."""
    topics = load_topics()
    for topic in topics:
        if topic["id"] == topic_id:
            topic["posted"] = True
            topic["posted_on"] = date.today().isoformat()
    save_topics(topics)


def show_progress():
    """Print how many topics are done."""
    topics = load_topics()
    done = sum(1 for topic in topics if topic["posted"])
    print(f"📊 Progress: {done}/{len(topics)} topics posted")