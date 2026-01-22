import os
import re
import sqlite3

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from gemini_message import generate_kudos_message

load_dotenv()

# Load Slack credentials
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

# Initialize Slack app (Socket Mode)
app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)

# Kudos detection pattern: "<@U12345> ++ optional message"
# Uses non-greedy match and lookahead to support multiple kudos in one message
# e.g., "<@U123> ++ great work <@U456> ++ awesome job"
MENTION_PLUS_PATTERN = re.compile(r"<@([A-Z0-9]+)>\s*\+\+\s*(.*?)(?=<@[A-Z0-9]+>\s*\+\+|$)")

# --- SQLite setup ---
DB_PATH = os.getenv("DB_PATH", "/home/ubuntu/kudos.db")

def init_db():
    """Create table if not exists."""
    print("Running with DB_PATH: ", DB_PATH)
    with sqlite3.connect(DB_PATH) as conn:
        # Aggregated kudos count table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kudos (
                user_id TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0
            )
        """)
        # Detailed kudos log table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kudos_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receiver_id TEXT NOT NULL,
                giver_id TEXT NOT NULL,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def increment_kudos(user_id: str, giver_id: str = None, message: str = None):
    """Increment kudos count for a user and log the transaction."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Update aggregated count
        cursor.execute("""
            INSERT INTO kudos (user_id, count)
            VALUES (?, 1)
            ON CONFLICT(user_id)
            DO UPDATE SET count = count + 1;
        """, (user_id,))
        # Log the transaction
        if giver_id:
            cursor.execute("""
                INSERT INTO kudos_log (receiver_id, giver_id, message)
                VALUES (?, ?, ?)
            """, (user_id, giver_id, message))
        conn.commit()

def get_kudos(user_id: str) -> int:
    """Return current kudos count."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count FROM kudos WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else 0

def get_leaderboard(limit: int = 10):
    """Return top N users."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, count FROM kudos ORDER BY count DESC LIMIT ?", (limit,))
        return cursor.fetchall()

# Initialize database
init_db()

# --- Slack Event Handlers ---

@app.event("message")
def handle_message_events(event, say):
    user = event.get("user")
    text = event.get("text", "")
    thread_ts = event.get("thread_ts") or event.get("ts")  # reply in same thread

    if not text or not user:
        return

    matches = MENTION_PLUS_PATTERN.findall(text)
    for target_user_id, message in matches:
        if target_user_id == user:
            say(
                text=f"Nice try <@{user}> 😜 You can’t give kudos to yourself!",
                thread_ts=thread_ts
            )
            continue

        # Extract and clean the message (strip whitespace)
        kudos_message = message.strip() if message else None
        
        # Save kudos with giver, timestamp (auto), and message
        increment_kudos(target_user_id, giver_id=user, message=kudos_message)
        new_count = get_kudos(target_user_id)
        
        # Generate an encouraging AI message
        ai_message = generate_kudos_message(
            kudos_message=kudos_message,
            kudos_count=new_count
        )
        
        say(
            text=f":sparkles: <@{target_user_id}> now has *{new_count}* kudos! {ai_message}",
            thread_ts=thread_ts
        )

@app.event("app_mention")
def show_help_or_leaderboard(event, say):
    text = event.get("text", "").lower()
    thread_ts = event.get("thread_ts") or event.get("ts")

    if "leaderboard" in text:
        leaderboard = get_leaderboard()
        if not leaderboard:
            say("No kudos given yet! Be the first to appreciate someone with `@user ++` 🎉", thread_ts=thread_ts)
            return
        message = ":trophy: *Kudos Leaderboard:*\n"
        for rank, (user_id, count) in enumerate(leaderboard, start=1):
            message += f"{rank}. <@{user_id}> — {count} kudos\n"
        say(message, thread_ts=thread_ts)
    else:
        say(
            "Hey there! 👋\n"
            "Give someone kudos with `@username ++`\n"
            "Or mention me with `leaderboard` to see the top users.",
            thread_ts=thread_ts
        )

if __name__ == "__main__":
    print("🚀 Kudos bot is running (Socket Mode)...")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()

