import os
import time
import json
import re
import requests
from typing import Type, Optional, Any, Dict, List
from pydantic import BaseModel, ValidationError

from backend.config import settings
from backend.logging_config import ai_logger
from backend.services.ai.base import AIProvider

class OpenRouterProvider(AIProvider):
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_MODEL
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.default_temp = settings.OPENROUTER_TEMPERATURE
        self.max_tokens = settings.OPENROUTER_MAX_TOKENS

    def is_configured(self) -> bool:
        key = os.getenv("OPENROUTER_API_KEY", self.api_key)
        return bool(key and len(key.strip()) > 5)

    def test_connection(self) -> Dict[str, Any]:
        """Tests OpenRouter AI connection, model availability, and measures latency."""
        key = os.getenv("OPENROUTER_API_KEY", self.api_key)
        if not self.is_configured():
            return {
                "ok": False,
                "configured": False,
                "error": "OpenRouter API key is not set. Add OPENROUTER_API_KEY in .env or Settings.",
                "model": self.model
            }
        start = time.time()
        try:
            content = self._call_api(
                system_prompt="You are a ping test assistant. Reply strictly with 'OK'.",
                user_prompt="Ping test",
                temperature=0.1
            )
            latency_ms = int((time.time() - start) * 1000)
            return {
                "ok": True,
                "configured": True,
                "model": os.getenv("OPENROUTER_MODEL", self.model) or "meta-llama/llama-3.3-70b-instruct",
                "latency_ms": latency_ms,
                "reply": content.strip()[:20]
            }
        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            return {
                "ok": False,
                "configured": True,
                "model": os.getenv("OPENROUTER_MODEL", self.model) or "meta-llama/llama-3.3-70b-instruct",
                "latency_ms": latency_ms,
                "error": str(e)
            }

    def _extract_json_substring(self, text: str) -> str:
        """Extracts clean JSON substring from raw response, stripping thinking monologues and markdown."""
        text = text.strip()

        # 1. Strip reasoning and thinking tokens (<think>...</think>, Thought process, etc.)
        text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"<thought>[\s\S]*?</thought>", "", text, flags=re.IGNORECASE).strip()

        # If model emitted closing </think> without opening <think>
        if "</think>" in text:
            text = text.split("</think>", 1)[-1].strip()

        # Strip unformatted "Thinking Process: ... \n\n" headers before JSON
        if "thinking process:" in text.lower():
            json_pos = min([p for p in [text.find("```"), text.find("{"), text.find("[")] if p != -1], default=-1)
            if json_pos != -1:
                text = text[json_pos:].strip()

        # 2. Look for markdown code block ```json ... ``` or unclosed ```json ...
        match = re.search(r"```(?:json)?\s*([\s\S]*?)(?:```|$)", text, re.IGNORECASE)
        if match and match.group(1).strip():
            candidate = match.group(1).strip()
            c_start = candidate.find("{")
            c_arr = candidate.find("[")
            if c_start != -1 or c_arr != -1:
                first_idx = min([i for i in [c_start, c_arr] if i != -1])
                candidate = candidate[first_idx:]
            return candidate

        # 3. Find first '{' and last '}'
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]

        # 4. Or array '[' and ']'
        start_arr = text.find("[")
        end_arr = text.rfind("]")
        if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
            return text[start_arr:end_arr+1]

        return text

    def _call_api(self, system_prompt: str, user_prompt: str, temperature: Optional[float] = None) -> str:
        if not self.is_configured():
            raise ValueError(
                "OpenRouter API key is missing. Please set OPENROUTER_API_KEY in your .env or Kaggle environment."
            )

        api_key = os.getenv("OPENROUTER_API_KEY", self.api_key)
        model = os.getenv("OPENROUTER_MODEL", self.model) or "meta-llama/llama-3.3-70b-instruct"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://aimoviestudio.local",
            "X-Title": "AI Movie Studio",
            "Content-Type": "application/json"
        }

        # Candidate models prioritized for fast, reliable, direct JSON output
        candidate_models = [model]
        for fallback in [
            "meta-llama/llama-3.3-70b-instruct",
            "mistralai/mistral-small-24b-instruct-2501",
            "qwen/qwen-2.5-72b-instruct",
            "qwen/qwen3.5-flash-02-23",
            "deepseek/deepseek-chat"
        ]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        last_error = ""
        for current_model in candidate_models:
            payload = {
                "model": current_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature if temperature is not None else self.default_temp,
                "max_tokens": self.max_tokens
            }

            ai_logger.info(f"Calling OpenRouter model={current_model} with user prompt length={len(user_prompt)}")

            try:
                resp = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    ai_logger.info(f"OpenRouter response received successfully using model={current_model}")
                    return content

                err_msg = f"OpenRouter API returned error HTTP {resp.status_code}: {resp.text}"
                ai_logger.warning(err_msg)
                last_error = err_msg

                # If 404 or model not found, try next candidate model
                if resp.status_code == 404 or "no endpoints found" in resp.text.lower():
                    ai_logger.info(f"Model '{current_model}' unavailable on OpenRouter (404). Trying next fallback model...")
                    continue
                else:
                    raise RuntimeError(err_msg)
            except requests.exceptions.RequestException as e:
                ai_logger.error(f"OpenRouter network request failed: {str(e)}")
                raise RuntimeError(f"OpenRouter request failed: {str(e)}")

        raise RuntimeError(f"OpenRouter failed across all tested model endpoints. Last error: {last_error}")

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None
    ) -> str:
        return self._call_api(system_prompt, user_prompt, temperature)

    def _normalize_dict(self, data: Any, response_model: Type[BaseModel]) -> Any:
        if isinstance(data, list):
            # If model expects a dict with a list field (e.g. 'clips' or 'scenes')
            fields = response_model.model_fields
            for f_name, f_info in fields.items():
                if f_name in ("clips", "scenes", "characters", "locations"):
                    return {f_name: data, "clip_count": len(data)}
            return data

        if not isinstance(data, dict):
            return data

        # If data is nested under model name e.g. {"ClipContinuityPlan": {...}}
        model_name = response_model.__name__
        if model_name in data and isinstance(data[model_name], dict):
            data = data[model_name]
        elif model_name.lower() in data and isinstance(data[model_name.lower()], dict):
            data = data[model_name.lower()]

        # If model echoed schema properties
        if "properties" in data and isinstance(data["properties"], dict):
            data = data["properties"]

        # Ensure clip_count is populated if clips exists
        if "clips" in data and isinstance(data["clips"], list):
            if "clip_count" not in data or not data["clip_count"]:
                data["clip_count"] = len(data["clips"])

        return data

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel],
        temperature: Optional[float] = None
    ) -> BaseModel:
        # Append schema instructions
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        enriched_system = (
            f"{system_prompt}\n\n"
            f"CRITICAL REQUIREMENT: You MUST respond ONLY with a valid JSON object matching the following structure. "
            f"Do NOT output schema metadata like '$defs' or 'properties'. Output the real content values directly in JSON format.\n"
            f"SCHEMA:\n{schema_json}"
        )

        # First attempt
        raw_output = self._call_api(enriched_system, user_prompt, temperature)
        cleaned_json = self._extract_json_substring(raw_output)

        try:
            parsed = json.loads(cleaned_json)
            normalized = self._normalize_dict(parsed, response_model)
            return response_model.model_validate(normalized)
        except (json.JSONDecodeError, ValidationError) as first_err:
            ai_logger.warning(f"First JSON validation attempt failed: {str(first_err)}. Attempting structured repair retry...")

            # Retry with explicit error feedback
            retry_prompt = (
                f"Your previous response produced a validation error: {str(first_err)}\n\n"
                f"Previous output was:\n{raw_output[:800]}\n\n"
                f"Please fix and output ONLY the valid JSON with actual values directly (do NOT include $defs or schemas):\n{schema_json}"
            )
            try:
                raw_retry = self._call_api(enriched_system, retry_prompt, temperature=0.2)
                cleaned_retry = self._extract_json_substring(raw_retry)
                parsed_retry = json.loads(cleaned_retry)
                normalized_retry = self._normalize_dict(parsed_retry, response_model)
                return response_model.model_validate(normalized_retry)
            except Exception as final_err:
                ai_logger.error(f"Structured JSON validation failed after retry: {str(final_err)}")
                raise ValueError(
                    f"AI Director returned invalid structure: {str(final_err)}"
                )
