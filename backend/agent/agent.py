"""
IT Support AI Agent
Uses browser-use + OpenRouter to navigate the admin panel and complete IT tasks.
"""

import asyncio
import os
import re

from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser   # ✅ FIXED (removed BrowserConfig)


ADMIN_PANEL_URL = os.getenv("ADMIN_PANEL_URL", "http://localhost:8000")


def build_system_prompt() -> str:
    return f"""You are an IT support AI agent with access to a web-based admin panel at {ADMIN_PANEL_URL}.

You complete IT support tasks by navigating the admin panel like a human would — clicking links, filling in forms, and submitting them.

Available pages:
- {ADMIN_PANEL_URL}/users                → List / search all users
- {ADMIN_PANEL_URL}/users/create         → Create a new user
- {ADMIN_PANEL_URL}/users/reset-password → Reset a user's password
- {ADMIN_PANEL_URL}/users/licenses       → Assign or revoke a software license
- {ADMIN_PANEL_URL}/users/toggle-status  → Activate or deactivate a user account
- {ADMIN_PANEL_URL}/audit-log            → View history of all actions

Rules:
1. Always navigate to the correct page.
2. Fill ALL required fields.
3. Confirm success message.
4. Report clearly if user not found.
5. Always give final summary.
"""


async def run_agent(task: str, headless: bool = True) -> dict:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")

    # ✅ LLM (OpenRouter)
    llm = ChatOpenAI(
        model="deepseek/deepseek-r1",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0,
        max_tokens=1000,
    )

    # ✅ IMPORTANT FIX (remove unsupported format)
    llm.model_kwargs.pop("response_format", None)

    # ✅ FIXED browser (NO BrowserConfig)
    browser = Browser(headless=headless)

    clean_task = f"{build_system_prompt()}\n\nTask: {task}"

    agent = Agent(
        task=clean_task,
        llm=llm,
        browser=browser,
        use_vision=False,
    )

    try:
        result = await agent.run(max_steps=20)

        final_result = (
            result.final_result()
            if hasattr(result, "final_result")
            else str(result)
        )

        return {
            "success": True,
            "result": final_result or "Task completed successfully",
            "steps": len(result.history) if hasattr(result, "history") else 0,
        }

    except Exception as e:
        return {
            "success": False,
            "result": f"Error: {str(e)}",
            "steps": 0,
        }

    finally:
        await browser.close()


# ─── Conditional Tasks ─────────────────────────────────

def build_conditional_task(raw: str) -> str:
    lower = raw.lower()

    if "if not" in lower and ("create" in lower or "assign" in lower):
        email_match = re.search(r"[\w.+-]+@[\w-]+\.\w+", raw)
        email = email_match.group(0) if email_match else "user"

        return (
            f"{raw}\n\n"
            f"Steps:\n"
            f"1. Check {ADMIN_PANEL_URL}/users for {email}\n"
            f"2. If not exists → create user\n"
            f"3. Then continue task\n"
            f"4. Give summary"
        )

    return raw


# ─── CLI TEST ─────────────────────────────────────────

if __name__ == "__main__":
    import sys

    task_input = " ".join(sys.argv[1:]) or "List users"
    task_input = build_conditional_task(task_input)

    print(f"\n🤖 Running Agent...\nTask: {task_input}\n")

    result = asyncio.run(run_agent(task_input, headless=False))

    print("\n" + "=" * 50)
    print("SUCCESS" if result["success"] else "FAILED")
    print(result["result"])