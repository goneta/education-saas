import json
import logging
import os
import re
from typing import Any, Dict, List, Literal, Optional, TypedDict

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from .. import crypto_utils, models

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - depends on deployment dependencies
    OpenAI = None

logger = logging.getLogger(__name__)
load_dotenv()
if os.getenv("APP_ENV") == "production":
    load_dotenv(".env.production", override=True)


class AIResponse(TypedDict):
    type: Literal["chat", "content"]
    message: str
    data: Optional[Any]
    provider_id: Optional[int]
    model_name: Optional[str]
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]


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

    def generate_response(self, message: str, user_context: Optional[Dict[str, Any]] = None) -> AIResponse:
        if not message.strip():
            return {
                "type": "chat",
                "message": "Please enter a question or request for the school assistant.",
                "data": None,
                "provider_id": None,
                "model_name": None,
                "prompt_tokens": None,
                "completion_tokens": None,
            }

        if self.client:
            return self._call_openai(message, user_context or {})

        return self._call_fallback(message, user_context or {})

    def generate_response_from_config(self, message: str, user_context: Optional[Dict[str, Any]], db: Session) -> AIResponse:
        """Call the first active DB-configured AI provider, with fallback by priority.

        API keys are decrypted only in memory, never returned by API routes. Providers
        that expose an OpenAI-compatible endpoint can be used through `base_url`.
        Providers without a supported SDK/base URL are skipped until their adapter is
        configured, then the next active provider is tried.
        """
        providers = db.query(models.AIProvider).filter(models.AIProvider.is_active == True).order_by(models.AIProvider.priority.asc()).all()  # noqa: E712
        failures: list[str] = []
        for provider in providers:
            try:
                response = self._call_configured_provider(message, user_context or {}, provider)
                response["provider_id"] = provider.id
                response["model_name"] = response.get("model_name") or provider.default_model
                return response
            except Exception as exc:  # pragma: no cover - external provider failure path
                logger.warning(
                    "Configured AI provider failed; trying next provider",
                    extra={"provider_id": provider.id, "provider_type": provider.provider_type, "model": provider.default_model},
                    exc_info=True,
                )
                failures.append(f"{provider.name}: {exc}")
                continue
        fallback = self.generate_response(message, user_context or {})
        fallback["provider_id"] = None
        fallback["model_name"] = self.model if self.client else "local-fallback"
        if failures:
            fallback["message"] = f"{fallback['message']} Fallback active apres echec fournisseur: {'; '.join(failures[:2])}."
        return fallback

    def _call_configured_provider(self, message: str, user_context: Dict[str, Any], provider: models.AIProvider) -> AIResponse:
        from .ai_provider_bootstrap import env_api_key_for

        provider_type = (provider.provider_type or "").lower()
        api_key = crypto_utils.decrypt_secret(provider.api_key_encrypted) if provider.api_key_encrypted else None
        if not api_key:
            # Fall back to the provider's .env.production key when no DB key is stored.
            api_key = env_api_key_for(provider_type)
        if not api_key:
            raise RuntimeError("missing API key (DB and environment)")
        if not OpenAI:
            raise RuntimeError("openai package unavailable")
        if provider_type not in {"openai", "openrouter", "grok", "custom", "manus", "claude", "anthropic", "gemini"}:
            raise RuntimeError(f"unsupported provider type {provider.provider_type}")
        if provider_type in {"claude", "anthropic", "gemini", "manus"} and not provider.base_url:
            raise RuntimeError("provider requires an OpenAI-compatible base_url or a dedicated adapter")
        client_kwargs: Dict[str, Any] = {"api_key": api_key}
        if provider.base_url:
            client_kwargs["base_url"] = provider.base_url
        client = OpenAI(**client_kwargs)
        return self._call_openai_client(client, provider.default_model or self.model, message, user_context, suppress_errors=False)

    def _iter_clients(self, db: Session):
        """Yield (client, model) for active configured providers (priority order),
        then the env fallback client. Used by lightweight LLM calls (e.g. routing)
        that don't need the full chat pipeline. Yields nothing when no provider is
        usable, so callers degrade gracefully."""
        from .ai_provider_bootstrap import env_api_key_for

        if OpenAI:
            providers = (
                db.query(models.AIProvider)
                .filter(models.AIProvider.is_active == True)  # noqa: E712
                .order_by(models.AIProvider.priority.asc())
                .all()
            )
            for provider in providers:
                try:
                    provider_type = (provider.provider_type or "").lower()
                    api_key = crypto_utils.decrypt_secret(provider.api_key_encrypted) if provider.api_key_encrypted else None
                    if not api_key:
                        api_key = env_api_key_for(provider_type)
                    if not api_key:
                        continue
                    if provider_type in {"claude", "anthropic", "gemini", "manus"} and not provider.base_url:
                        continue
                    client_kwargs: Dict[str, Any] = {"api_key": api_key}
                    if provider.base_url:
                        client_kwargs["base_url"] = provider.base_url
                    yield OpenAI(**client_kwargs), provider.default_model or self.model
                except Exception:  # pragma: no cover - provider construction failure
                    continue
        if self.client:
            yield self.client, self.model

    def route_to_agent(self, message: str, agent_options: List[Dict[str, str]], db: Session) -> Optional[str]:
        """LLM router: pick the single best agent key for a message.

        Returns a validated key, or None when no provider is configured or the
        model fails / returns an unknown key — callers then fall back to keyword
        routing. Cheap, deterministic prompt; no chat history or RBAC payload.
        """
        if not message or not agent_options:
            return None
        allowed = {opt["key"] for opt in agent_options}
        system = (
            "You route requests in the TeducAI multi-agent system. Given a user "
            "message and a list of agents (key + domain), choose the single most "
            'appropriate agent. Reply ONLY with JSON: {"agent_key": "<one of the '
            'provided keys>"}. If none clearly fits, use "coordinator".'
        )
        payload = json.dumps({"message": message[:2000], "agents": agent_options}, ensure_ascii=False)
        for client, model in self._iter_clients(db):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": payload},
                    ],
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content or "{}"
                key = (self._parse_json_response(content).get("agent_key") or "").strip()
                if key in allowed:
                    return key
            except Exception as exc:  # pragma: no cover - external service failure path
                logger.warning("agent router call failed: %s", exc)
                continue
        return None

    def generate_vision_response(self, prompt: str, image_base64: str, mime_type: str, db: Session) -> Dict[str, Any]:
        """Call the first active provider with an image (OpenAI-compatible
        multimodal content parts — works for OpenAI directly and for Anthropic
        through its OpenAI-compatible /v1 endpoint).

        Vision has NO local fallback: when no vision-capable provider is
        reachable a RuntimeError is raised, so callers can surface an honest
        503 instead of fabricating an OCR result. Requires a vision-capable
        `default_model` on the provider (e.g. gpt-4.1-mini/gpt-4o for OpenAI,
        claude-3-5-sonnet for Anthropic)."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}},
                ],
            }
        ]
        failures: list[str] = []
        for client, model in self._iter_clients(db):
            try:
                response = client.chat.completions.create(model=model, messages=messages)
                content = response.choices[0].message.content or ""
                usage = getattr(response, "usage", None)
                return {
                    "content": content,
                    "model_name": model,
                    "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
                    "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
                }
            except Exception as exc:  # pragma: no cover - external provider failure path
                logger.warning("Vision provider failed; trying next provider", exc_info=True)
                failures.append(str(exc))
                continue
        raise RuntimeError(
            "No vision-capable AI provider is reachable. Configure OpenAI (OPENAI_API_KEY) "
            "or Anthropic (ANTHROPIC_API_KEY) with a vision-capable model."
            + (f" Last errors: {'; '.join(failures[:2])}" if failures else "")
        )

    def _call_openai(self, message: str, user_context: Dict[str, Any]) -> AIResponse:
        return self._call_openai_client(self.client, self.model, message, user_context)

    def _call_openai_client(self, client: Any, model: str, message: str, user_context: Dict[str, Any], *, suppress_errors: bool = True) -> AIResponse:
        try:
            system_prompt = """
You are TeducAI, an expert assistant for a school-management SaaS platform.
You must strictly obey the connected user's RBAC context. Never reveal, infer,
fetch, or claim access to data outside the user's school, children, student
profile, assigned class scope, or effective permissions. If a request is outside
the allowed scope, refuse with the exact refusal sentence supplied in context.
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

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "system", "content": json.dumps({"rbac_context": user_context}, ensure_ascii=False)},
                    {"role": "user", "content": message},
                ],
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content or "{}"
            parsed = self._parse_json_response(content)
            normalized = self._normalize_response(parsed)
            usage = getattr(response, "usage", None)
            normalized["model_name"] = model
            normalized["prompt_tokens"] = getattr(usage, "prompt_tokens", None) if usage else None
            normalized["completion_tokens"] = getattr(usage, "completion_tokens", None) if usage else None
            return normalized
        except Exception as exc:  # pragma: no cover - external service failure path
            logger.exception("AI provider call failed: %s", exc)
            if not suppress_errors:
                raise
            return {
                "type": "chat",
                "message": "The AI provider is temporarily unavailable. Please try again shortly.",
                "data": None,
                "provider_id": None,
                "model_name": model,
                "prompt_tokens": None,
                "completion_tokens": None,
            }

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse provider JSON without failing on markdown fences or preambles."""
        stripped = content.strip()
        if not stripped:
            return {}
        try:
            parsed = json.loads(stripped)
            return parsed if isinstance(parsed, dict) else {"type": "content", "message": "Resultat genere.", "data": parsed}
        except json.JSONDecodeError:
            fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
            if fenced:
                parsed = json.loads(fenced.group(1))
                return parsed if isinstance(parsed, dict) else {"type": "content", "message": "Resultat genere.", "data": parsed}
            start = stripped.find("{")
            end = stripped.rfind("}")
            if start != -1 and end > start:
                parsed = json.loads(stripped[start:end + 1])
                return parsed if isinstance(parsed, dict) else {"type": "content", "message": "Resultat genere.", "data": parsed}
            logger.warning("AI provider returned non-JSON content; wrapping as content preview")
            return {"type": "content", "message": "Resultat IA genere.", "data": stripped}

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

        return {"type": response_type, "message": message, "data": data, "provider_id": None, "model_name": None, "prompt_tokens": None, "completion_tokens": None}

    def _call_fallback(self, message: str, user_context: Dict[str, Any]) -> AIResponse:
        msg_lower = message.lower()
        role = user_context.get("role", "utilisateur")
        scope = user_context.get("scope_summary", "vos donnees autorisees")

        if any(keyword in msg_lower for keyword in ["course", "curriculum", "lesson", "cours", "leçon"]):
            return {
                "type": "content",
                "message": f"J'ai prepare un brouillon pedagogique adapte a votre role ({role}) et limite a {scope}.",
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
                "provider_id": None,
                "model_name": "local-fallback",
                "prompt_tokens": None,
                "completion_tokens": None,
            }

        if any(keyword in msg_lower for keyword in ["report", "list", "rapport", "liste"]):
            return {
                "type": "content",
                "message": f"J'ai prepare un brouillon structure dans le perimetre autorise pour votre role ({role}).",
                "data": """## School Operations Checklist

1. Verify pupil registration records.
2. Confirm teacher timetable completeness.
3. Review recent attendance anomalies.
4. Check pending fee payments and recorded expenses.
5. Generate academic reports for the selected term.
""",
                "provider_id": None,
                "model_name": "local-fallback",
                "prompt_tokens": None,
                "completion_tokens": None,
            }

        return {
            "type": "chat",
            "message": (
                f"Je peux vous aider dans le perimetre de votre role ({role}): {scope}. "
                "Le fournisseur IA complet n'est pas configure dans cet environnement; j'utilise donc une reponse locale securisee."
            ),
            "data": None,
            "provider_id": None,
            "model_name": "local-fallback",
            "prompt_tokens": None,
            "completion_tokens": None,
        }


ai_service = AIService()
