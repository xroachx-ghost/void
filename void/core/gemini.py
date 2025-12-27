"""
Gemini AI assistant helper.

Provides a lightweight wrapper for Gemini API calls and agent-style task updates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Iterable, Mapping, Sequence
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

    def __init__(
        self,
        api_key: str,
        model: str | None = None,
        api_base: str | None = None,
        system_instruction: str | None = None,
        extra_payload: Mapping[str, Any] | None = None,
        generation_config: Mapping[str, Any] | None = None,
        timeout: int | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model or Config.GEMINI_MODEL
        self.api_base = api_base or Config.GEMINI_API_BASE
        self.system_instruction = system_instruction
        self.extra_payload = dict(extra_payload or {})
        self.generation_config = dict(generation_config or {})
        self.timeout = timeout or Config.TIMEOUT_MEDIUM

    def generate(
        self,
        prompt: str,
        tasks: Iterable[dict[str, str]] | None = None,
        history: Sequence[Mapping[str, Any]] | None = None,
        parts: Sequence[Mapping[str, Any]] | None = None,
        extra_payload: Mapping[str, Any] | None = None,
    ) -> GeminiAgentResult:
        prompt = (prompt or "").strip()
        if not prompt:
            return GeminiAgentResult(success=False, message="Enter a message to send.")

        if not self.api_key:
            return GeminiAgentResult(success=False, message="Gemini API key is required.")

        task_list = list(tasks or [])
        full_prompt = prompt
        if task_list:
            task_context = json.dumps(task_list, indent=2)
            full_prompt = (
                f"Current tasks:\\n{task_context}\\n\\n"
                f"User message: {prompt}"
            )

        resolved_parts = list(parts or [])
        if not resolved_parts:
            resolved_parts = [{"text": full_prompt}]

        contents = list(history or [])
        contents.append({"role": "user", "parts": resolved_parts})

        payload: dict[str, Any] = {
            "contents": contents,
        }

        if self.system_instruction:
            payload["systemInstruction"] = {
                "role": "system",
                "parts": [{"text": self.system_instruction}],
            }

        generation_config = {
            "temperature": 0.2,
            "maxOutputTokens": 2048,
            **self.generation_config,
        }
        if generation_config:
            payload["generationConfig"] = generation_config

        payload = self._merge_payload(payload, self.extra_payload)
        payload = self._merge_payload(payload, extra_payload)

        url = f"{self.api_base}/{self.model}:generateContent?key={self.api_key}"

        try:
            request = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw_response = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            return GeminiAgentResult(
                success=False,
                message="Unable to reach Gemini API. Check your network or API key.",
                raw={"error": str(exc)},
            )

        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            return GeminiAgentResult(
                success=False,
                message="Gemini response could not be parsed.",
                raw={"error": str(exc), "raw": raw_response},
            )

        candidate = (parsed.get("candidates") or [{}])[0]
        content = candidate.get("content") or {}
        parts_payload = content.get("parts") or []
        response_text = self._extract_text(parts_payload)

        structured = None
        normalized_tasks: list[dict[str, str]] = []
        if response_text:
            try:
                structured_payload = json.loads(response_text)
                if isinstance(structured_payload, dict):
                    structured = structured_payload
            except json.JSONDecodeError:
                structured = None

        if structured:
            response_text = str(structured.get("response") or response_text or "")
            tasks_payload = structured.get("tasks") or []
            normalized_tasks = self._normalize_tasks(tasks_payload)

        return GeminiAgentResult(
            success=True,
            message="Gemini response received.",
            response=response_text or "",
            tasks=normalized_tasks,
            raw={"response": parsed, "structured": structured},
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

    def _extract_text(self, parts: Iterable[Mapping[str, Any]]) -> str:
        chunks: list[str] = []
        for part in parts:
            text = part.get("text") if isinstance(part, Mapping) else None
            if text:
                chunks.append(str(text))
        return "".join(chunks).strip()

    def _merge_payload(
        self,
        base: dict[str, Any],
        override: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        if not override:
            return base
        merged = dict(base)
        for key, value in override.items():
            if value is None:
                merged.pop(key, None)
                continue
            if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
                merged[key] = self._merge_payload(dict(merged[key]), value)
            else:
                merged[key] = value
        return merged
