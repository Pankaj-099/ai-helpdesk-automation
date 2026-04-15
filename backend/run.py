import asyncio
import os

# ✅ Fix Playwright issue
asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from slack_bot.bot import start_slack_bot
import uvicorn

async def main():
    # ✅ Start Slack bot separately
    if os.getenv("SLACK_BOT_TOKEN"):
        asyncio.create_task(start_slack_bot())

    # ✅ Start FastAPI
    config = uvicorn.Config("main:app", port=8000, reload=True)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())