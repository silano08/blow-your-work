import asyncio
import json
import os
import re
from copilot import CopilotClient
from copilot.session_events import AssistantMessageData, SessionIdleData
from copilot.session import PermissionHandler

from app.models import SubTask


SYSTEM_PROMPT = """You are a personal productivity assistant.
When the user describes a goal, break it down into 3-7 concrete, actionable subtasks.
Respond ONLY with a valid JSON array (no markdown, no extra text) in this exact format:
[
  {"title": "...", "detail": "...", "priority": "high|medium|low"},
  ...
]
Priority rules: "high" = must do first / blocking, "medium" = normal, "low" = nice to have."""


async def breakdown_goal(goal: str, model: str = "gpt-4.1") -> list[SubTask]:
    collected = []
    done = asyncio.Event()

    async with CopilotClient(
        github_token=os.getenv("GITHUB_TOKEN")
    ) as client:
        async with await client.create_session(
            on_permission_request=PermissionHandler.approve_all,
            model=model,
        ) as session:

            def on_event(event):
                match event.data:
                    case AssistantMessageData() as data:
                        collected.append(data.content)
                    case SessionIdleData():
                        done.set()

            session.on(on_event)
            await session.send(f"{SYSTEM_PROMPT}\n\nGoal: {goal}")
            await done.wait()

    raw = "".join(collected).strip()

    # Extract JSON array even if wrapped in markdown code fences
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        raise ValueError(f"Copilot returned unexpected format: {raw[:200]}")

    items = json.loads(match.group())
    return [SubTask(**item) for item in items]
