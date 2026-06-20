"""Azure OpenAI (Foundry) 기반 AI 추천 서비스.

Copilot SDK 는 Todo ↔ 전제 기여도 분석에 사용하고,
팀 목표 기반 할일 추천은 Azure OpenAI API 를 직접 사용합니다.
환경변수:
  AZURE_OPENAI_ENDPOINT   예: https://<resource>.openai.azure.com/
  AZURE_OPENAI_API_KEY    API 키
  AZURE_OPENAI_DEPLOYMENT 배포명 (기본: gpt-4o)
  AZURE_OPENAI_API_VERSION API 버전 (기본: 2025-01-01-preview)
"""
from __future__ import annotations

import json
import os
import re

import httpx

ENDPOINT    = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
API_KEY     = os.getenv("AZURE_OPENAI_API_KEY", "")
DEPLOYMENT  = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

SUGGEST_SYSTEM = """You are a team productivity coach.
Given a team's OKR premises (이니셔티브/목표), generate 4 concrete, actionable todo suggestions for today.
Each suggestion must be directly tied to one of the premises.

Respond ONLY with a valid JSON array (no markdown):
[
  {
    "title": "<Korean todo title, ≤30 chars>",
    "premise_id": <id>,
    "premise_type": "initiative" | "goal",
    "premise_title": "<premise title>"
  }
]
Rules:
- All titles must be in Korean
- Mix initiatives and goals (2 each if possible)
- Be specific and actionable, not vague
- No more than 4 items"""


async def suggest_team_todos(team_id: int, premises: list[dict]) -> list[dict]:
    """Azure OpenAI 로 팀 전제 기반 오늘 할일 4개를 추천합니다.

    Azure 환경변수 미설정 시 빠른 폴백 응답을 반환합니다.
    """
    if not ENDPOINT or not API_KEY:
        return _fallback_suggestions(premises)

    premises_text = "\n".join(
        f"[id={p['id']}, type={p['type']}] {p['title']}"
        + (f" — {p.get('description', '')}" if p.get("description") else "")
        for p in premises
        if p.get("is_active")
    )

    url = f"{ENDPOINT}/openai/deployments/{DEPLOYMENT}/chat/completions?api-version={API_VERSION}"
    headers = {"api-key": API_KEY, "Content-Type": "application/json"}
    body = {
        "messages": [
            {"role": "system", "content": SUGGEST_SYSTEM},
            {
                "role": "user",
                "content": f"Team {team_id} premises:\n{premises_text}\n\nSuggest 4 todos for today.",
            },
        ],
        "max_tokens": 500,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=12) as client:
        resp = await client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()

    m = re.search(r"\[.*\]", content, re.DOTALL)
    if not m:
        return _fallback_suggestions(premises)
    return json.loads(m.group())


def _fallback_suggestions(premises: list[dict]) -> list[dict]:
    """Azure 미설정 시 전제 기반 규칙형 추천."""
    # DB 구버전 grand/small → initiative/goal 매핑
    type_map = {"grand": "initiative", "initiative": "initiative",
                "small": "goal", "goal": "goal"}
    active = [p for p in premises if p.get("is_active")]
    suggestions = []
    for p in active[:4]:
        keyword = re.sub(r"(하기|강화|확보|달성|개선|높이기)$", "", p["title"])
        ptype = type_map.get(p.get("type", "initiative"), "initiative")
        suggestions.append({
            "title": f"{keyword} 관련 오늘 실행 항목 정리",
            "premise_id": p["id"],
            "premise_type": ptype,
            "premise_title": p["title"],
        })
    return suggestions[:4]
