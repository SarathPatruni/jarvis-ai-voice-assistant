import json

import jarvis.commands as commands
import jarvis.memory as memory


def test_local_greeting_short_circuits_before_gemini(monkeypatch):
    calls = []

    def fake_understand_request(*args, **kwargs):
        calls.append("gemini")
        return {"type": "general_question", "intent": "answer", "answer": "ignored"}

    monkeypatch.setattr(commands, "understand_request", fake_understand_request)

    ok, reply = commands.process_request("hi jar", use_voice=False, history=[])

    assert ok is True
    assert reply == "Hello! Nice to meet you."
    assert calls == []


def test_local_command_short_circuits_before_gemini(monkeypatch):
    calls = []

    def fake_open_calculator():
        calls.append("calculator")
        return True

    def fake_understand_request(*args, **kwargs):
        calls.append("gemini")
        return {"type": "general_question", "intent": "answer", "answer": "ignored"}

    monkeypatch.setattr(commands, "open_calculator", fake_open_calculator)
    monkeypatch.setattr(commands, "understand_request", fake_understand_request)

    ok, reply = commands.process_request("open calculator", use_voice=False, history=[])

    assert ok is True
    assert reply == "Opening Calculator."
    assert calls == ["calculator"]


def test_wikipedia_request_bypasses_gemini(monkeypatch):
    calls = []

    def fake_search_wikipedia(query):
        calls.append(query)
        return "Python is a programming language."

    def fake_understand_request(*args, **kwargs):
        calls.append("gemini")
        return {"type": "wikipedia", "intent": "search", "topic": "Python"}

    monkeypatch.setattr(commands, "search_wikipedia", fake_search_wikipedia)
    monkeypatch.setattr(commands, "understand_request", fake_understand_request)

    ok, reply = commands.process_request("wikipedia Python", use_voice=False, history=[])

    assert ok is True
    assert reply == "Python is a programming language."
    assert calls == ["Python"]


def test_wikipedia_prompt_asks_for_topic_without_gemini(monkeypatch):
    calls = []

    def fake_understand_request(*args, **kwargs):
        calls.append("gemini")
        return {"type": "general_question", "intent": "answer", "answer": "ignored"}

    monkeypatch.setattr(commands, "understand_request", fake_understand_request)

    ok, reply = commands.process_request("Wikipedia", use_voice=False, history=[])

    assert ok is True
    assert reply == "Sure. What topic should I search on Wikipedia?"
    assert calls == []


def test_wikipedia_follow_up_uses_recent_history(monkeypatch):
    calls = []

    def fake_search_wikipedia(query):
        calls.append(query)
        return "Python is a high-level language."

    monkeypatch.setattr(commands, "search_wikipedia", fake_search_wikipedia)

    history = [
        {"user": "Wikipedia", "jarvis": "Sure. What topic should I search on Wikipedia?"},
    ]
    ok, reply = commands.process_request("Python", use_voice=False, history=history)

    assert ok is True
    assert reply == "Python is a high-level language."
    assert calls == ["Python"]


def test_wikipedia_follow_up_applies_instruction(monkeypatch):
    monkeypatch.setattr(
        commands,
        "search_wikipedia",
        lambda query: "Python is a language. It is widely used. It is readable.",
    )
    history = [
        {"user": "Wikipedia", "jarvis": "Sure. What topic should I search on Wikipedia?"},
    ]

    ok, reply = commands.process_request(
        "tell me about Python in two lines",
        use_voice=False,
        history=history,
    )

    assert ok is True
    assert reply == "Python is a language. It is widely used."


def test_exit_intent_stops_processing(monkeypatch):
    monkeypatch.setattr(
        commands,
        "understand_request",
        lambda *args, **kwargs: {"type": "command", "intent": "exit"},
    )

    ok, reply = commands.process_request("please stop", use_voice=False, history=[])

    assert ok is False
    assert reply == "Goodbye. See you later."


def test_general_question_uses_answer_from_single_gemini_response(monkeypatch):
    calls = []

    def fake_understand_request(*args, **kwargs):
        calls.append("gemini")
        return {
            "type": "general_question",
            "intent": "answer",
            "answer": "Recursion is when a function calls itself.",
        }

    monkeypatch.setattr(commands, "understand_request", fake_understand_request)

    ok, reply = commands.process_request("Explain recursion simply", use_voice=False, history=[])

    assert ok is True
    assert reply == "Recursion is when a function calls itself."
    assert len(calls) == 1


def test_gemini_503_message_is_safe(monkeypatch):
    def fake_understand_request(*args, **kwargs):
        return {"type": "error", "safe_message": "Gemini is temporarily unavailable. Please try again in a moment."}

    monkeypatch.setattr(commands, "understand_request", fake_understand_request)
    ok, reply = commands.process_request("Explain recursion simply", use_voice=False, history=[])

    assert ok is True
    assert reply == "Gemini is temporarily unavailable. Please try again in a moment."


def test_gemini_429_message_is_safe(monkeypatch):
    def fake_understand_request(*args, **kwargs):
        return {"type": "error", "safe_message": "Gemini is rate-limited right now. Please try again in a moment."}

    monkeypatch.setattr(commands, "understand_request", fake_understand_request)
    ok, reply = commands.process_request("What is AI?", use_voice=False, history=[])

    assert ok is True
    assert reply == "Gemini is rate-limited right now. Please try again in a moment."


def test_memory_clear_conversations_clears_persistent_history(tmp_path, monkeypatch):
    file = tmp_path / "conversation.json"
    file.write_text(json.dumps([{"user": "hi", "jarvis": "hello"}]), encoding="utf-8")
    monkeypatch.setattr(memory, "MEMORY_FILE", file)

    assert memory.clear_conversations() is True
    assert memory.load_conversations() == []


def test_memory_save_and_load_round_trip(tmp_path, monkeypatch):
    file = tmp_path / "conversation.json"
    monkeypatch.setattr(memory, "MEMORY_FILE", file)

    assert memory.save_conversation("hello", "hi") is True
    assert memory.load_conversations() == [{"user": "hello", "jarvis": "hi"}]
