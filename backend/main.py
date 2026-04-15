"""
Main FastAPI application
"""

import asyncio

# ✅ Required for Playwright on Windows
asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import logging
import os

from dotenv import load_dotenv
load_dotenv()   # ✅ load .env variables

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from admin_panel.routes import router as admin_router
from agent.agent import run_agent, build_conditional_task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── App ─────────────────────────────────────────────

app = FastAPI(
    title="IT Support Agent",
    description="AI-powered IT admin panel with browser-use agent",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)

# ─── Slack Bot Startup (FINAL FIX) ───────────────────

@app.on_event("startup")
async def start_slack():
    slack_bot_token = os.getenv("SLACK_BOT_TOKEN")
    slack_app_token = os.getenv("SLACK_APP_TOKEN")

    if slack_bot_token and slack_app_token:
        try:
            from slack_bot.bot import start_slack_bot
            asyncio.create_task(start_slack_bot())
            logger.info("✅ Slack bot started")
        except ImportError:
            logger.warning("slack-bolt not installed; Slack disabled")
    else:
        logger.warning("❌ Slack tokens missing — Slack disabled")

# ─── Agent API ───────────────────────────────────────

class AgentRequest(BaseModel):
    task: str


class AgentResponse(BaseModel):
    success: bool
    result: str
    steps: int
    task: str


@app.post("/api/agent", response_model=AgentResponse)
async def run_agent_endpoint(req: AgentRequest):

    if not req.task.strip():
        raise HTTPException(status_code=400, detail="Task cannot be empty")

    task = build_conditional_task(req.task.strip())
    logger.info(f"Agent task: {task}")

    result = await run_agent(task, headless=True)

    return AgentResponse(
        success=result["success"],
        result=result["result"],
        steps=result["steps"],
        task=req.task,
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}