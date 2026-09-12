import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

_GEMINI_CLIENT = None
MODEL = "gemini-3.6-flash"
ALLOWED_COMMANDS = {
    "open_chrome",
    "open_calculator",
    "open_notepad",
    "play_music",
    "exit",
}


def _client():
    global _GEMINI_CLIENT
    if _GEMINI_CLIENT is not None:
        return _GEMINI_CLIENT
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    _GEMINI_CLIENT = genai.Client(api_key=api_key)
    return _GEMINI_CLIENT


def _history_text(history, limit=8):
    if not history:
        return "No previous conversation is available."
    recent = history[-limit:]
    lines = []
    for item in recent:
        user_text = (item.get("user") or "").strip()
        jarvis_text = (item.get("jarvis") or "").strip()
        if user_text or jarvis_text:
            lines.append(f"User: {user_text}\nJarvis: {jarvis_text}")
    return "\n".join(lines) if lines else "No previous conversation is available."


def _safe_error_message(error):
    error_code = getattr(error, "code", None) or getattr(error, "status_code", None)
    text = str(error).lower()
    if error_code == 429 or "429" in text or "resource exhausted" in text:
        return "Gemini is rate-limited right now. Please try again in a moment."
    if error_code == 503 or "503" in text or "temporarily unavailable" in text or "service unavailable" in text:
        return "Gemini is temporarily unavailable. Please try again in a moment."
    if error_code in {401, 403} or "unauthorized" in text or "permission denied" in text:
        return "Gemini authentication failed. Check GEMINI_API_KEY or GOOGLE_API_KEY."
    if error_code == 400 or "invalid argument" in text or "bad request" in text:
        return "Gemini rejected the request. Please try asking in a different way."
    if error_code == 404 or "not found" in text:
        return f"The Gemini model {MODEL} is not available for this API key."
    if "api key" in text or "missing" in text:
        return "Gemini is not configured. Add GEMINI_API_KEY to your environment."
    if "connection" in text or "timed out" in text or "network" in text:
        return "I couldn't connect to Gemini right now. Please try again in a moment."
    return "Gemini is temporarily unavailable. Please try again in a moment."


def _generate_content(client, contents, config=None):
    for attempt in range(3):
        try:
            kwargs = {"model": MODEL, "contents": contents}
            if config is not None:
                kwargs["config"] = config
            return client.models.generate_content(**kwargs)
        except Exception as error:
            error_code = getattr(error, "code", None) or getattr(error, "status_code", None)
            if error_code != 503 and "503" not in str(error):
                raise
            print(f"Gemini 503 on attempt {attempt + 1}/3: {error}")
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def _clean_json_text(raw_text):
    text = (raw_text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "json" in text.lower().splitlines()[0].lower():
            lines = text.splitlines()[1:]
            text = "\n".join(lines)
    return text.strip()


def _route_schema():
    return {
        "type": "OBJECT",
        "properties": {
            "type": {
                "type": "STRING",
                "enum": ["command", "wikipedia", "general_question"],
            },
            "intent": {
                "type": "STRING",
                "enum": ["answer", "search", "open_chrome", "open_calculator", "open_notepad", "play_music", "exit"],
            },
            "topic": {"type": "STRING"},
            "instruction": {"type": "STRING"},
            "query": {"type": "STRING"},
            "answer": {"type": "STRING"},
        },
        "required": ["type", "intent", "topic", "instruction", "query", "answer"],
    }


def route_request(prompt, history=None):
    client = _client()
    if client is None:
        return {
            "type": "error",
            "intent": "error",
            "topic": "",
            "instruction": "",
            "query": prompt,
            "answer": "Gemini is not configured. Add GEMINI_API_KEY to your environment.",
            "safe_message": "Gemini is not configured. Add GEMINI_API_KEY to your environment.",
        }

    try:
        response = _generate_content(
            client,
            contents=(
                "You are a routing layer for a Python personal assistant. "
                "Return only valid JSON matching the schema. "
                "Use type='command' only for safe allowlisted automation actions. "
                "Use type='wikipedia' for explicit Wikipedia requests or follow-ups about a known topic. "
                "Use type='general_question' for questions that should be answered directly. "
                "For command requests, intent must be one of: open_chrome, open_calculator, open_notepad, play_music, exit. "
                "For wikipedia, put the topic in 'topic' and any format request in 'instruction'. "
                "For general questions, provide the answer directly in 'answer'. "
                "Do not invent commands or execute arbitrary shell commands. "
                "Use recent conversation only when it is needed for a follow-up.\n\n"
                f"Recent conversation:\n{_history_text(history)}\n\nUser request: {prompt}"
            ),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=_route_schema(),
            ),
        )
        payload_text = _clean_json_text(getattr(response, "text", ""))
        if not payload_text:
            raise ValueError("Gemini returned an empty routing response")
        result = json.loads(payload_text)
        if not isinstance(result, dict):
            raise ValueError("Gemini returned a non-object routing result")

        result_type = result.get("type")
        if result_type not in {"command", "wikipedia", "general_question"}:
            raise ValueError("Gemini returned an unsupported request type")

        if result_type == "command":
            intent = result.get("intent", "")
            if intent not in ALLOWED_COMMANDS:
                raise ValueError("Gemini returned an unsupported command intent")

        payload = {
            "type": result_type,
            "intent": result.get("intent", "answer"),
            "topic": (result.get("topic") or "").strip(),
            "instruction": (result.get("instruction") or "").strip(),
            "query": (result.get("query") or "").strip(),
            "answer": (result.get("answer") or "").strip(),
        }
        return payload
    except Exception as error:
        print(f"Gemini routing error: {error}")
        return {
            "type": "error",
            "intent": "error",
            "topic": "",
            "instruction": "",
            "query": prompt,
            "answer": "",
            "safe_message": _safe_error_message(error),
        }


def understand_request(prompt, history=None):
    return route_request(prompt, history)


def ask_gemini(prompt, history=None, source=None):
    client = _client()
    if client is None:
        return "Gemini is not configured. Add GEMINI_API_KEY to your environment."

    source_text = f"\nReference information:\n{source}" if source else ""
    try:
        response = _generate_content(
            client,
            contents=(
                "You are Jarvis, a concise and helpful personal assistant. "
                "Answer clearly and use plain text. For follow-up questions, reference the recent conversation when needed.\n\n"
                f"Recent conversation:\n{_history_text(history)}\n\n"
                f"User request: {prompt}{source_text}"
            ),
        )
        return (getattr(response, "text", "") or "").strip() or "Jarvis returned an empty answer."
    except Exception as error:
        print(f"Gemini answer error: {error}")
        return _safe_error_message(error)