import json
import logging
import os
from typing import Any, Dict, Literal, Optional, TypedDict

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - depends on deployment dependencies
    OpenAI = None

logger = logging.getLogger(__name__)


class AIResponse(TypedDict):
    type: Literal["chat", "content"]
    message: str
    data: Optional[Any]


class AIService:
    """AI assistant service used by the dashboard chat panel.

    The service uses an OpenAI-compatible client when `OPENAI_API_KEY` is
    configured. In local or demo environments without a key, it returns a
    deterministic fallback response instead of failing the whole chat endpoint.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.client = None

        if self.api_key and OpenAI:
            base_url = os.getenv("OPENAI_BASE_URL")
            client_kwargs: Dict[str, Any] = {"api_key": self.api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            self.client = OpenAI(**client_kwargs)
        else:
            logger.warning(
                "AI service is running in local fallback mode because OPENAI_API_KEY "
                "is not configured or the openai package is unavailable."
            )

    def generate_response(self, message: str) -> AIResponse:
        if not message.strip():
            return {
                "type": "chat",
                "message": "Please enter a question or request for the school assistant.",
                "data": None,
            }

        if self.client:
            return self._call_openai(message)

        return self._call_fallback(message)

    def _call_openai(self, message: str) -> AIResponse:
        try:
            system_prompt = """
You are TeducAI, an expert assistant for a school-management SaaS platform.
Return only a JSON object with this exact structure:
{
  "type": "chat" | "content",
  "message": "short conversational response for the user",
  "data": null | "Markdown content when the answer should open in the preview panel"
}
Use `content` when the user asks you to draft a course, report, letter, list,
policy, lesson plan, parent-support text, or administrative document. Use `chat`
for short guidance and operational answers. Keep school data privacy in mind.
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message},
                ],
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content or "{}"
            parsed = json.loads(content)
            return self._normalize_response(parsed)
        except Exception as exc:  # pragma: no cover - external service failure path
            logger.exception("AI provider call failed: %s", exc)
            return {
                "type": "chat",
                "message": "The AI provider is temporarily unavailable. Please try again shortly.",
                "data": None,
            }

    def _normalize_response(self, value: Dict[str, Any]) -> AIResponse:
        response_type = value.get("type") if value.get("type") in {"chat", "content"} else "chat"
        message = value.get("message")
        data = value.get("data")

        if not isinstance(message, str) or not message.strip():
            message = "I prepared a response for you."

        if response_type == "chat":
            data = None
        elif data is not None and not isinstance(data, str):
            data = json.dumps(data, ensure_ascii=False, indent=2)

        return {"type": response_type, "message": message, "data": data}

    def _call_fallback(self, message: str) -> AIResponse:
        msg_lower = message.lower()

        if any(keyword in msg_lower for keyword in ["course", "curriculum", "lesson", "cours", "leçon"]):
            return {
                "type": "content",
                "message": "I drafted a lesson outline that you can review in the preview panel.",
                "data": """# Lesson Outline: Introduction to Digital Skills

## Learning Objectives

Students will understand basic digital safety, responsible device usage, and how to organize school work with simple productivity tools.

## Session Plan

1. **Warm-up discussion** about how students currently use digital tools.
2. **Mini-lesson** on passwords, privacy, and respectful communication.
3. **Guided activity** where students organize a sample assignment folder.
4. **Reflection** on one safe digital habit to apply at home.

## Assessment

Teachers can assess participation, completion of the guided activity, and the quality of the final reflection.
""",
            }

        if any(keyword in msg_lower for keyword in ["report", "list", "rapport", "liste"]):
            return {
                "type": "content",
                "message": "I prepared a structured draft in the preview panel.",
                "data": """## School Operations Checklist

1. Verify pupil registration records.
2. Confirm teacher timetable completeness.
3. Review recent attendance anomalies.
4. Check pending fee payments and recorded expenses.
5. Generate academic reports for the selected term.
""",
            }

        return {
            "type": "chat",
            "message": (
                "The AI provider is not configured in this environment, so I am using a local fallback response. "
                "Configure OPENAI_API_KEY to enable full AI-assisted parent support and document generation."
            ),
            "data": None,
        }


ai_service = AIService()
