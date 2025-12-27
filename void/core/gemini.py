"""
Gemini AI assistant helper.

Provides a lightweight wrapper for Gemini API calls and agent-style task updates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Iterable
import urllib.error
import urllib.request

from ..config import Config


@dataclass
class GeminiAgentResult:
    success: bool
    message: str
    response: str = ""
    tasks: list[dict[str, str]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


class GeminiAgent:
    """Gemini agent wrapper that returns responses plus an updated task list."""

    def __init__(self, api_key: str, model: str | None = None) -> None:
        self.api_key = api_key
        self.model = model or Config.GEMINI_MODEL

    def generate(
        self,
        prompt: str,
        tasks: Iterable[dict[str, str]] | None = None,
    ) -> GeminiAgentResult:
        prompt = (prompt or "").strip()
        if not prompt:
            return GeminiAgentResult(success=False, message="Enter a message to send.")

        if not self.api_key:
            return GeminiAgentResult(success=False, message="Gemini API key is required.")

        task_list = list(tasks or [])
        system_instruction = (
            "You are a planning agent for the Void Suite GUI. "
            "Return ONLY JSON with keys: response (string) and tasks (array). "
            "Each task must include title and status. "
            "Statuses: todo, in_progress, done. "
            "Use the provided task list as the current state and update it as needed. "
            "Add, remove, or update tasks to achieve the user's goal."
        )
        task_context = json.dumps(task_list, indent=2)
        full_prompt = (
            f"Current tasks:\\n{task_context}\\n\\n"
            f"User message: {prompt}"
        )

        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": full_prompt}]},
            ],
            "systemInstruction": {
                "role": "system",
                "parts": [{"text": system_instruction}],
            },
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
            },
        }

        url = f"{Config.GEMINI_API_BASE}/{self.model}:generateContent?key={self.api_key}"

        try:
            request = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=Config.TIMEOUT_MEDIUM) as response:
                raw_response = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            return GeminiAgentResult(
                success=False,
                message="Unable to reach Gemini API. Check your network or API key.",
                raw={"error": str(exc)},
            )

        try:
            parsed = json.loads(raw_response)
            content = parsed["candidates"][0]["content"]["parts"][0]["text"]
            structured = json.loads(content)
        except (KeyError, IndexError, json.JSONDecodeError, TypeError) as exc:
            return GeminiAgentResult(
                success=False,
                message="Gemini response could not be parsed.",
                raw={"error": str(exc), "raw": raw_response},
            )

        response_text = str(structured.get("response") or "")
        tasks_payload = structured.get("tasks") or []
        normalized_tasks = self._normalize_tasks(tasks_payload)
        return GeminiAgentResult(
            success=True,
            message="Gemini response received.",
            response=response_text,
            tasks=normalized_tasks,
            raw=structured,
        )

    def _normalize_tasks(self, tasks: Iterable[Any]) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        for task in tasks:
            if not isinstance(task, dict):
                continue
            title = str(task.get("title") or "").strip()
            status = str(task.get("status") or "todo").strip().lower()
            if not title:
                continue
            if status not in {"todo", "in_progress", "done"}:
                status = "todo"
            normalized.append({"title": title, "status": status})
        return normalized
