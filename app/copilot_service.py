"""Copilot SDK 기반 AI 분석 서비스."""
import asyncio
import json
import os
import re

from copilot import CopilotClient
from copilot.session_events import AssistantMessageData, SessionIdleData
from copilot.session import PermissionHandler


ANALYSIS_PROMPT = """You are a team productivity analyst.
You will be given a list of team premises (대전제/소전제) and a todo item.
Analyze whether the todo contributes to any of the premises.

Respond ONLY with a valid JSON object (no markdown, no extra text):
{
  "premise_id": <number or null>,
  "relation": "initiative" | "goal" | "none",
  "confidence": <float 0.0-1.0>,
  "reason": "<Korean explanation in 1-2 sentences>"
}

Rules:
- "initiative" = todo directly contributes to an initiative (대전제 category)
- "goal" = todo directly contributes to a specific goal (소전제)
- "none" = no clear connection
- Choose the MOST relevant premise if multiple match
- Be strict: confidence > 0.7 only for clear matches
- reason must be in Korean"""

ANALYSIS_FALLBACK = {
    "premise_id": None,
    "relation": "none",
    "confidence": 0.0,
    "reason": "분석 실패",
}


async def analyze_todo_premise(
    todo_title: str,
    todo_detail: str,
    premises: list[dict],
    model: str = "gpt-4.1",
) -> dict:
    """Copilot SDK로 Todo가 어떤 전제에 기여하는지 분석합니다."""
    if not premises:
        return {"premise_id": None, "relation": "none", "confidence": 0.0, "reason": "등록된 전제가 없습니다."}

    premises_text = "\n".join(
        f"[id={p['id']}, type={p['type']}] {p['title']}"
        + (f" — {p['description']}" if p.get("description") else "")
        for p in premises
    )

    prompt = f"""{ANALYSIS_PROMPT}

Premises:
{premises_text}

Todo:
- title: {todo_title}
- detail: {todo_detail or '(없음)'}

Analyze which premise this todo contributes to."""

    collected = []
    done = asyncio.Event()

    async with CopilotClient(github_token=os.getenv("GITHUB_TOKEN")) as client:
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
            await session.send(prompt)
            await done.wait()

    raw = "".join(collected).strip()
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        raise ValueError(f"Copilot analysis returned unexpected format: {raw[:200]}")

    result = json.loads(m.group())
    return {
        "premise_id": result.get("premise_id"),
        "relation": result.get("relation", "none"),
        "confidence": float(result.get("confidence", 0.0)),
        "reason": result.get("reason", ""),
    }


async def analyze_todos_batch(
    todos: list[dict],
    premises: list[dict],
    model: str = "gpt-4.1",
) -> list[dict]:
    """여러 Todo를 배치로 분석합니다 (최대 5개씩 병렬)."""
    async def _analyze_one(todo: dict) -> dict:
        for attempt in range(3):
            try:
                result = await asyncio.wait_for(
                    analyze_todo_premise(
                        todo_title=todo["title"],
                        todo_detail=todo.get("detail", ""),
                        premises=premises,
                        model=model,
                    ),
                    timeout=30,
                )
                return {"todo_id": todo["id"], **result}
            except (json.JSONDecodeError, ValueError):
                if attempt >= 2:
                    return {"todo_id": todo["id"], **ANALYSIS_FALLBACK}
            except asyncio.TimeoutError:
                if attempt >= 2:
                    return {"todo_id": todo["id"], **ANALYSIS_FALLBACK}
            except Exception:
                if attempt >= 2:
                    return {"todo_id": todo["id"], **ANALYSIS_FALLBACK}

        return {"todo_id": todo["id"], **ANALYSIS_FALLBACK}

    results = []
    for i in range(0, len(todos), 5):
        batch = todos[i:i + 5]
        batch_results = await asyncio.gather(*[_analyze_one(t) for t in batch])
        results.extend(batch_results)

    return results
