import sys
from datetime import date, datetime
from writer import create_post, save_post
from memory import get_next_topic, mark_posted, show_progress, load_topics
from tools import research_topic
from linkedin import post_to_linkedin
from email_approval import send_email, wait_for_reply

AUTO_MODE = "--auto" in sys.argv
MIN_SCORE_TO_PUBLISH = 8
APPROVAL_MINUTES = 120


def keep_laptop_awake():
    """Ask Windows not to sleep while the agent is waiting for your reply."""
    try:
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
    except Exception:
        pass


def already_posted_today():
    today = date.today().isoformat()
    return any(topic.get("posted_on") == today for topic in load_topics())


def publish(topic, post, path):
    """Publish and return the link, or None if it failed."""
    try:
        url = post_to_linkedin(post)
        print(f"✅ Published! {url}")
        mark_posted(topic["id"])
        show_progress()
        return url
    except Exception as error:
        print(f"❌ Could not publish: {error}")
        print(f"   The post is saved here: {path}")
        return None


def email_approval_flow(topic, post, score, path):
    code = f"#{topic['id']}-{datetime.now():%H%M}"

    if score < MIN_SCORE_TO_PUBLISH:
        print(f"🛑 Score {score}/10 is too low. Not publishing.")
        send_email(f"[LinkedIn Agent {code}] Skipped today",
                   f"Today's draft only scored {score}/10, so I didn't publish it.\n\n"
                   f"It's saved at: {path}\n\n{post}")
        return

    send_email(
        f"[LinkedIn Agent {code}] Draft: {topic['topic']}",
        f"Here's today's LinkedIn post (score {score}/10).\n\n"
        f"Reply NO to cancel, or YES to publish now.\n"
        f"If you don't reply within {APPROVAL_MINUTES // 60} hours, I'll publish it automatically.\n\n"
        f"{'=' * 40}\n{post}\n{'=' * 40}",
    )
    print("📧 Draft emailed to you.")

    decision = wait_for_reply(code, minutes=APPROVAL_MINUTES)

    if decision == "NO":
        print("❌ You said NO. Not publishing.")
        send_email(f"[LinkedIn Agent {code}] Cancelled",
                   "OK, I didn't publish it. I'll try this topic again tomorrow.")
        return

    url = publish(topic, post, path)
    if url:
        send_email(f"[LinkedIn Agent {code}] Published ✅",
                   f"Your post is live!\n{url}\n\n{post}")
    else:
        send_email(f"[LinkedIn Agent {code}] Publishing failed ❌",
                   f"Something went wrong. The post is saved at: {path}")


def run_agent():
    mode = "AUTO" if AUTO_MODE else "MANUAL"
    print(f"\n===== Agent run: {datetime.now():%Y-%m-%d %H:%M} | mode: {mode} =====")
    show_progress()

    if AUTO_MODE:
        keep_laptop_awake()
        if already_posted_today():
            print("⏭️ Already posted today. Skipping.")
            return

    topic = get_next_topic()
    if topic is None:
        print("🎉 All topics are posted! Add more to topics.json.")
        return

    print(f"\n📌 Next topic (#{topic['id']}): {topic['topic']}")
    print(f"   Phase: {topic['phase']} | Style: {topic['style']}\n")

    full_topic = f"{topic['topic']} (part of my {topic['phase']} learning series)"

    print("🔍 Researching the topic...")
    research = research_topic(topic["topic"])
    if research:
        print("\n📝 Research notes:\n" + research + "\n")

    post, score = create_post(full_topic, topic["style"], research)
    path = save_post(post)

    print("\n" + "=" * 50)
    print(post)
    print("=" * 50)
    print(f"\n💾 Saved to: {path}")

    if AUTO_MODE:
        email_approval_flow(topic, post, score, path)
    else:
        answer = input("\n📤 Publish this to LinkedIn now? (y/n): ")
        if answer.lower() == "y":
            publish(topic, post, path)
        else:
            print("👍 Not published. I'll suggest this topic again next time.")


if __name__ == "__main__":
    run_agent()