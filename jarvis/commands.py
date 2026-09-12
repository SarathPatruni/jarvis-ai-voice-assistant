import re

try:
    from .automation import open_notepad, open_calculator, open_chrome, play_music
    from .services import search_wikipedia
    from .speech import listen, speak
except ImportError:
    try:
        from jarvis.automation import open_notepad, open_calculator, open_chrome, play_music
        from jarvis.services import search_wikipedia
        from jarvis.speech import listen, speak
    except ImportError:  # pragma: no cover - fallback only for partial installs
        def open_notepad():
            return False

        def open_calculator():
            return False

        def open_chrome():
            return False

        def play_music():
            return False

        def search_wikipedia(_query):
            return "I couldn't connect to Wikipedia right now."

        def listen():
            return ""

        def speak(_text):
            return False

try:
    from .gemini import ask_gemini, understand_request
except ImportError:
    from jarvis.gemini import ask_gemini, understand_request


def _status(status_callback, value):
    if status_callback:
        status_callback(value)


def _extract_explicit_wikipedia_topic(command):
    normalized = (command or "").strip()
    lowered = normalized.lower()
    if lowered.startswith("wikipedia "):
        return normalized[len("wikipedia "):].strip()
    if lowered.startswith("search wikipedia for "):
        return normalized[len("search wikipedia for "):].strip()
    if "wikipedia" in lowered and "for" in lowered:
        match = re.search(r"wikipedia\s+for\s+(.+)", lowered)
        if match:
            return match.group(1).strip()
    return ""


def _format_wikipedia_summary(summary, instruction):
    if not isinstance(summary, str) or not summary.strip():
        return summary or "I couldn't find a Wikipedia result for that topic."
    summary = summary.strip()
    instruction_text = (instruction or "").strip().lower()
    if not instruction_text:
        return summary

    if "two lines" in instruction_text or "2 lines" in instruction_text:
        sentences = re.split(r"(?<=[.!?])\s+", summary)
        excerpt = " ".join(sentences[:2]).strip()
        return excerpt if excerpt else summary
    if "3 points" in instruction_text or "three points" in instruction_text:
        sentences = re.split(r"(?<=[.!?])\s+", summary)
        bullets = [f"- {sentence.strip()}" for sentence in sentences[:3] if sentence.strip()]
        return "\n".join(bullets) if bullets else summary
    if "short" in instruction_text or "brief" in instruction_text:
        return summary.split(". ", 1)[0].strip() if ". " in summary else summary
    return summary


def _local_command_response(command):
    normalized = re.sub(r"\s+", " ", (command or "").strip()).lower()

    if re.fullmatch(r"(?:hi|hello|hey)(?:\s+(?:jar|jarvis))?\s*", normalized):
        return "Hello! Nice to meet you.", True
    if normalized in {"how are you", "how are you doing", "how're you"}:
        return "I am doing great.", True
    if normalized in {"exit", "quit", "goodbye", "bye"}:
        return "Goodbye. See you later.", False
    if re.fullmatch(r"(?:please\s+)?(?:open|launch|start)\s+(?:the\s+)?(?:chrome|browser)\s*", normalized):
        return "open_chrome", True
    if re.fullmatch(r"(?:please\s+)?(?:open|launch|start)\s+(?:the\s+)?(?:calculator|calc)\s*", normalized):
        return "open_calculator", True
    if re.fullmatch(r"(?:please\s+)?(?:open|launch|start)\s+(?:the\s+)?(?:notepad|text editor)\s*", normalized):
        return "open_notepad", True
    if re.fullmatch(r"(?:play|start)\s+(?:some\s+)?music\s*", normalized):
        return "play_music", True
    return None, True


def _is_explicit_wikipedia_request(command):
    normalized = re.sub(r"\s+", " ", (command or "").strip()).lower()
    if normalized in {"wikipedia"}:
        return True
    if normalized.startswith("wikipedia "):
        return True
    if normalized.startswith("search wikipedia for "):
        return True
    if normalized.startswith("search ") and " on wikipedia" in normalized:
        return True
    if "wikipedia" in normalized and "for" in normalized:
        return True
    return False


def _extract_wikipedia_topic(command):
    normalized = re.sub(r"\s+", " ", (command or "").strip())
    lowered = normalized.lower()
    if lowered in {"wikipedia"}:
        return ""
    if lowered.startswith("wikipedia "):
        return normalized[len("wikipedia "):].strip()
    if lowered.startswith("search wikipedia for "):
        return normalized[len("search wikipedia for "):].strip()
    if lowered.startswith("search ") and " on wikipedia" in lowered:
        return normalized[len("search "):].split(" on wikipedia", 1)[0].strip()
    if "wikipedia" in lowered and "for" in lowered:
        match = re.search(r"wikipedia\s+for\s+(.+)", lowered)
        if match:
            return match.group(1).strip()
    return ""


def _should_use_wikipedia_follow_up(command, history=None):
    if not history:
        return False
    recent = history[-8:]
    if not recent:
        return False
    last_message = recent[-1]
    last_user = str(last_message.get("user") or "").strip().lower()
    last_assistant = str(last_message.get("jarvis") or "").strip().lower()
    if "what topic should i search on wikipedia" in last_assistant:
        return True
    if "wikipedia" in last_user and "what topic" in last_assistant:
        return True
    return False


def _extract_wikipedia_follow_up(command):
    text = re.sub(r"\s+", " ", (command or "").strip())
    match = re.match(r"(?:tell me about|search for|find)\s+(.+?)(?:\s+in\s+(.+))?$", text, re.IGNORECASE)
    if not match:
        return text, ""
    return match.group(1).strip(), (match.group(2) or "").strip()


def _execute_intent(intent):
    if intent == "open_notepad":
        return "Opening Notepad." if open_notepad() else "Notepad is not available in this environment."
    if intent == "open_calculator":
        return "Opening Calculator." if open_calculator() else "Calculator is not available in this environment."
    if intent == "open_chrome":
        return "Opening Chrome." if open_chrome() else "Chrome is not available in this environment."
    if intent == "play_music":
        return "Playing music." if play_music() else "Music playback is not available in this environment."
    if intent == "exit":
        return "Goodbye. See you later."
    return None


def process_request(command, use_voice=True, history=None, status_callback=None):
    command = (command or "").strip()
    if not command:
        return True, "Please say or type a command."

    direct_result, should_continue = _local_command_response(command)
    if direct_result is not None:
        if direct_result == "Goodbye. See you later.":
            if use_voice:
                _status(status_callback, "SPEAKING...")
                speak(direct_result)
            return False, direct_result
        if direct_result in {"Hello! Nice to meet you.", "I am doing great."}:
            if use_voice:
                _status(status_callback, "SPEAKING...")
                speak(direct_result)
            return True, direct_result
        if direct_result in {"open_chrome", "open_calculator", "open_notepad", "play_music"}:
            action_reply = _execute_intent(direct_result)
            if use_voice:
                _status(status_callback, "SPEAKING...")
                speak(action_reply)
            return should_continue, action_reply

    if _is_explicit_wikipedia_request(command):
        topic = _extract_wikipedia_topic(command)
        if not topic:
            reply = "Sure. What topic should I search on Wikipedia?"
        else:
            result = search_wikipedia(topic)
            reply = _format_wikipedia_summary(result, "")
        if use_voice:
            _status(status_callback, "SPEAKING...")
            speak(reply)
        return True, reply

    if _should_use_wikipedia_follow_up(command, history):
        topic, instruction = _extract_wikipedia_follow_up(command)
        result = search_wikipedia(topic)
        reply = _format_wikipedia_summary(result, instruction)
        if use_voice:
            _status(status_callback, "SPEAKING...")
            speak(reply)
        return True, reply

    _status(status_callback, "GEMINI THINKING...")
    intent_data = understand_request(command, history)
    request_type = intent_data.get("type")
    intent = intent_data.get("intent")

    if request_type == "command":
        reply = _execute_intent(intent) or "I can only open Chrome, Calculator, Notepad, or play music."
    elif request_type == "wikipedia":
        topic = (intent_data.get("topic") or "").strip() or _extract_explicit_wikipedia_topic(command)
        if not topic:
            reply = "Which topic should I search on Wikipedia?"
        else:
            source = search_wikipedia(topic)
            if not source or source.lower().startswith("i couldn't") or source.lower().startswith("something went wrong"):
                reply = source or "I couldn't find that topic on Wikipedia."
            else:
                instruction = (intent_data.get("instruction") or "").strip()
                reply = _format_wikipedia_summary(source, instruction)
    elif request_type == "general_question":
        reply = (intent_data.get("answer") or "").strip() or ask_gemini(command, history)
    elif request_type == "error":
        explicit_topic = _extract_explicit_wikipedia_topic(command)
        if explicit_topic:
            reply = search_wikipedia(explicit_topic)
        else:
            reply = intent_data.get("safe_message") or "Gemini is unavailable right now. Please try again shortly."
    else:
        reply = ask_gemini(command, history)

    if use_voice:
        _status(status_callback, "SPEAKING...")
        speak(reply)
    if intent == "exit":
        return False, reply
    return True, reply


def process_command(command, use_voice=True, history=None, status_callback=None):
    return process_request(command, use_voice=use_voice, history=history, status_callback=status_callback)
