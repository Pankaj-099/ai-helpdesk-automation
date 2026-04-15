#!/usr/bin/env python3
"""
Quick CLI to test the agent locally without starting the full server.

Usage:
  python run_agent.py "reset password for john@company.com to NewPass@99"
  python run_agent.py "create user Alice Brown, alice@company.com, Engineer, Engineering"
  python run_agent.py "assign GitHub license to sarah@company.com"
  python run_agent.py "check if alice@company.com exists, if not create them, then assign Figma license"
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load .env from backend/
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Make sure backend/ is on the path
sys.path.insert(0, os.path.dirname(__file__))

from agent.agent import run_agent, build_conditional_task


async def main():
    task_input = " ".join(sys.argv[1:]).strip()
    if not task_input:
        print("Usage: python run_agent.py \"<your IT task>\"")
        print("\nExamples:")
        print('  python run_agent.py "reset password for john@company.com to NewPass@99"')
        print('  python run_agent.py "create user Alice Brown, alice@company.com, Engineer, Engineering"')
        print('  python run_agent.py "assign GitHub license to sarah@company.com"')
        sys.exit(1)

    task = build_conditional_task(task_input)

    print(f"\n{'─'*60}")
    print(f"🤖  IT Support Agent")
    print(f"{'─'*60}")
    print(f"Task : {task_input}")
    if task != task_input:
        print(f"Expanded task detected (multi-step)")
    print(f"{'─'*60}\n")

    result = await run_agent(task, headless=False)  # headless=False so you can watch

    print(f"\n{'─'*60}")
    if result["success"]:
        print(f"✅  Completed in {result['steps']} browser steps")
    else:
        print(f"❌  Failed")
    print(f"\nResult:\n{result['result']}")
    print(f"{'─'*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
