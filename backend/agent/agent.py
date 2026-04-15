"""
IT Support AI Agent
Uses browser-use + Gemini to navigate the admin panel and complete IT tasks.
"""

import asyncio
import os
import re
from typing import Optional

from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser, BrowserConfig


ADMIN_PANEL_URL = os.getenv("ADMIN_PANEL_URL", "http://localhost:8000")


def build_system_prompt() -> str:
    return f"""You are an IT support AI agent with access to a web-based admin panel at {ADMIN_PANEL_URL}.

You complete IT support tasks by navigating the admin panel like a human would — clicking links, filling in forms, and submitting them.

Available pages:
- {ADMIN_PANEL_URL}/users                → List / search all users
- {ADMIN_PANEL_URL}/users/create         → Create a new user (name, email, role, department, password)
- {ADMIN_PANEL_URL}/users/reset-password → Reset a user's password (email, new password, confirm password)
- {ADMIN_PANEL_URL}/users/licenses       → Assign or revoke a software license for a user
- {ADMIN_PANEL_URL}/users/toggle-status  → Activate or deactivate a user account
- {ADMIN_PANEL_URL}/audit-log            → View history of all actions

Rules:
1. Always navigate to the correct page for the task.
2. Fill in ALL required form fields before submitting.
3. After submitting, confirm success by reading the green success message on the page.
4. If a user is not found, report that clearly.
5. For conditional tasks (e.g. "check if user exists, if not create them"), first check /users, then act accordingly.
6. When creating a user, if no password is specified, use "Welcome@123" as the default.
7. When assigning a license, select the correct license from the dropdown and choose "Assign".
8. Always finish by summarising exactly what was done.
"""


async def run_agent(task: str, headless: bool = True) -> dict:
    """
    Run the AI agent to complete an IT support task.

    Args:
        task: Natural language task description
        headless: Run browser in headless mode (True for server, False for demo)

    Returns:
        dict with keys: success, result, steps
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")

    from langchain_openai import ChatOpenAI

    class SafeChatOpenAI(ChatOpenAI):

        def _get_request_payload(self, messages, stop=None, **kwargs):
            payload = super()._get_request_payload(messages, stop=stop, **kwargs)

            # ✅ FIX 1: remove json_schema
            payload.pop("response_format", None)

            # ✅ FIX 2: force ALL content → string
            for msg in payload.get("messages", []):
                if not isinstance(msg.get("content"), str):
                    msg["content"] = str(msg["content"])

            return payload


    llm = ChatOpenAI(
        model="deepseek/deepseek-r1",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0,
        max_tokens=1000
    )

    llm.model_kwargs.pop("response_format", None)

    browser = Browser(
        config=BrowserConfig(
            headless=headless,
            disable_security=True,
        )
    )

    clean_task = f"{build_system_prompt()}\n\nTask to complete: {task}"

    agent = Agent(
        task=clean_task,
        llm=llm,
        browser=browser,
        use_vision=False,
    )

    try:
        result = await agent.run(max_steps=20)
        final_result = result.final_result() if hasattr(result, "final_result") else str(result)
        return {
            "success": True,
            "result": final_result or "Task completed successfully.",
            "steps": len(result.history) if hasattr(result, "history") else 0,
        }
    except Exception as e:
        return {
            "success": False,
            "result": f"Agent encountered an error: {str(e)}",
            "steps": 0,
        }
    finally:
        await browser.close()


# ─── Conditional / Multi-step Tasks ──────────────────────────────────────────

def build_conditional_task(raw: str) -> str:
    """
    Detect common multi-step patterns and expand them into detailed instructions
    so the agent handles them correctly.
    """
    lower = raw.lower()

    # "check if user exists, if not create them, then assign a license"
    if "if not" in lower and ("create" in lower or "assign" in lower):
        email_match = re.search(r"[\w.+-]+@[\w-]+\.\w+", raw)
        email = email_match.group(0) if email_match else "the user"
        return (
            f"{raw}\n\n"
            f"Step-by-step instructions:\n"
            f"1. Go to {ADMIN_PANEL_URL}/users and search for {email}.\n"
            f"2. If the user exists, note their current state and continue to the next step.\n"
            f"3. If the user does NOT exist, go to {ADMIN_PANEL_URL}/users/create and create them.\n"
            f"4. After confirming user exists, complete any remaining actions (assign license, reset password, etc.).\n"
            f"5. Report a full summary of every action taken."
        )

    return raw


if __name__ == "__main__":
    import sys

    task_input = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "List all users"
    task_input = build_conditional_task(task_input)

    print(f"\n🤖 IT Agent starting...\nTask: {task_input}\n")
    result = asyncio.run(run_agent(task_input, headless=False))

    print("\n" + "─" * 50)
    if result["success"]:
        print(f"✅ Done in {result['steps']} steps")
    else:
        print("❌ Task failed")
    print(f"\nResult:\n{result['result']}")
