"""
Slack Bot for IT Agent
Listens for messages in a Slack channel and triggers the AI agent.
"""

import asyncio
import os
import logging

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from agent.agent import run_agent, build_conditional_task

logger = logging.getLogger(__name__)

# ─── SAFE APP INIT ───────────────────────────────────────

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

app = AsyncApp(token=SLACK_BOT_TOKEN)


# ─── SAFE TASK PARSER ────────────────────────────────────

def extract_task(text: str, bot_user_id: str = None) -> str:
    """Safely extract task text."""
    if not isinstance(text, str):
        return ""

    task = text.strip()

    if bot_user_id:
        task = task.replace(f"<@{bot_user_id}>", "").strip()

    return task


# ─── MENTION HANDLER ─────────────────────────────────────

@app.event("app_mention")
async def handle_mention(event, say, client):
    try:
        text = event.get("text", "")

        auth = await client.auth_test()
        bot_user_id = auth.get("user_id")

        task = extract_task(text, bot_user_id)

        if not task:
            await say("Hi! Mention me with a task like:\n`reset password for john@company.com`")
            return

        await say(f"⏳ Running: *{task}*")

        task = build_conditional_task(task)

        result = await run_agent(task, headless=False)

        if result.get("success"):
            await say(f"✅ Done ({result.get('steps', 0)} steps)\n\n{result.get('result')}")
        else:
            await say(f"❌ Failed\n\n{result.get('result')}")

    except Exception as e:
        logger.error(f"Slack mention error: {e}")
        await say("❌ Something went wrong while processing your request.")


# ─── DM HANDLER ─────────────────────────────────────────

@app.event("message")
async def handle_dm(message, say):
    try:
        # Ignore bots
        if message.get("subtype") or message.get("bot_id"):
            return

        # Only DMs
        if message.get("channel_type") != "im":
            return

        task = extract_task(message.get("text", ""))

        if not task:
            return

        await say(f"⏳ Running: *{task}*")

        task = build_conditional_task(task)

        result = await run_agent(task, headless=False)

        if result.get("success"):
            await say(f"✅ Done ({result.get('steps', 0)} steps)\n\n{result.get('result')}")
        else:
            await say(f"❌ Failed\n\n{result.get('result')}")

    except Exception as e:
        logger.error(f"Slack DM error: {e}")
        await say("❌ Error while processing your request.")


# ─── START BOT ──────────────────────────────────────────

async def start_slack_bot():
    if not SLACK_APP_TOKEN or not SLACK_BOT_TOKEN:
        logger.warning("Slack tokens missing — bot not started")
        return

    try:
        handler = AsyncSocketModeHandler(app, SLACK_APP_TOKEN)
        logger.info("🤖 Slack bot started")
        await handler.start_async()

    except Exception as e:
        logger.error(f"Slack startup error: {e}")