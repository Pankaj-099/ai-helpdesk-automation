"""
Slack Bot for IT Agent
Listens for messages in a Slack channel and triggers the AI agent.

Setup:
1. Create a Slack App at https://api.slack.com/apps
2. Enable Socket Mode
3. Subscribe to: app_mention, message.channels events
4. Add Bot Token Scopes: app_mentions:read, chat:write, channels:history
5. Set SLACK_BOT_TOKEN and SLACK_APP_TOKEN in .env
"""

import asyncio
import os
import logging
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from agent.agent import run_agent, build_conditional_task

logger = logging.getLogger(__name__)

app = AsyncApp(token=os.getenv("SLACK_BOT_TOKEN", ""))


@app.event("app_mention")
async def handle_mention(event, say, client):
    """Handle @mention in any channel."""
    # Strip the bot mention from the text
    text = event.get("text", "")
    bot_user_id = (await client.auth_test())["user_id"]
    task = text.replace(f"<@{bot_user_id}>", "").strip()

    if not task:
        await say("Hi! Mention me with an IT task, e.g. `@ITAgent reset password for john@company.com`")
        return

    await say(f"⏳ On it! Running: *{task}*")

    task = build_conditional_task(task)
    result = await run_agent(task, headless=True)

    if result["success"]:
        await say(f"✅ *Done* ({result['steps']} steps)\n\n{result['result']}")
    else:
        await say(f"❌ *Failed*\n\n{result['result']}")


@app.event("message")
async def handle_dm(message, say):
    """Handle direct messages to the bot."""
    # Ignore bot messages and subtypes
    if message.get("subtype") or message.get("bot_id"):
        return

    # Only handle DMs (channel type 'im')
    channel_type = message.get("channel_type")
    if channel_type != "im":
        return

    task = message.get("text", "").strip()
    if not task:
        return

    await say(f"⏳ Running: *{task}*")

    task = build_conditional_task(task)
    result = await run_agent(task, headless=True)

    if result["success"]:
        await say(f"✅ *Done* ({result['steps']} steps)\n\n{result['result']}")
    else:
        await say(f"❌ *Failed*\n\n{result['result']}")


async def start_slack_bot():
    """Start the Slack bot in Socket Mode."""
    app_token = os.getenv("SLACK_APP_TOKEN", "")
    if not app_token or not os.getenv("SLACK_BOT_TOKEN"):
        logger.warning("Slack tokens not set — bot will not start.")
        return

    handler = AsyncSocketModeHandler(app, app_token)
    logger.info("🤖 Slack bot started")
    await handler.start_async()
