from pathlib import Path
import sys

import streamlit as st
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))
from jarvis.commands import process_command
from jarvis.memory import clear_conversations, load_conversations, save_conversation
from jarvis.speech import listen

st.set_page_config(page_title="Jarvis", page_icon="J", layout="wide")

st.markdown(
	"""
	<style>
	@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');
	:root { --navy: #102a43; --muted: #627d98; --accent: #ef8354; --paper: #f7f3ed; --line: #d8e0e7; }
	.stApp { background: var(--paper); color: var(--navy); }
	[data-testid="stSidebar"] { background: var(--navy); }
	[data-testid="stSidebar"] * { color: #f7f3ed !important; }
	h1, h2, h3, p, label, button { font-family: 'Space Grotesk', sans-serif; }
	h1 { font-size: clamp(2.8rem, 7vw, 5rem) !important; letter-spacing: 0 !important; line-height: .95 !important; }
	.eyebrow { color: var(--accent); font: 500 .72rem 'DM Mono', monospace; letter-spacing: .12em; }
	.hero { border-bottom: 1px solid #c9d4df; padding: 2rem 0 1.25rem; margin-bottom: 1rem; }
	.hero p { color: var(--muted); max-width: 40rem; font-size: 1.05rem; }
	.status { background: #e4f0e9; color: #276749; padding: .7rem .85rem; font: 500 .78rem 'DM Mono', monospace; }
	.mic-panel { background: #fffdf9; border: 1px solid var(--line); border-radius: 12px; padding: 1.25rem; margin: 1.1rem 0; }
	.mic-label { color: var(--muted); font: 500 .72rem 'DM Mono', monospace; letter-spacing: .1em; }
	[data-testid="stChatMessage"] { border: 1px solid var(--line); background: rgba(255,255,255,.58); border-radius: 10px; }
	.stApp [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
	.stApp [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
	.stApp [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {
		color: #111827 !important;
	}
	.stButton button { border-radius: 7px; border: 1px solid var(--navy); min-height: 2.7rem; }
	[data-testid="stSidebar"] .stButton button { border-color: #7890a4; background: transparent; }
	</style>
	""",
	unsafe_allow_html=True,
)

def set_status(value):
	st.session_state.status = value
	if "status_box" in st.session_state:
		st.session_state.status_box.markdown(f'<div class="status">● {value}</div>', unsafe_allow_html=True)

def conversation_history():
	return load_conversations()[-8:]

def add_interaction(command, reply):
	st.session_state.messages.extend(
		[{"role": "user", "content": command}, {"role": "assistant", "content": reply}]
	)
	save_conversation(command, reply)

def run_text_command(command):
	if not command.strip():
		return
	set_status("PROCESSING...")
	_, reply = process_command(
		command,
	use_voice=False,
	history=conversation_history(),
	status_callback=set_status,
	)
	add_interaction(command, reply)
	set_status("READY")

def run_voice_command():
	set_status("LISTENING...")
	command = listen()
	if not command:
		set_status("READY")
		st.warning("I couldn't hear a command. Check your microphone and try again.")
		return
	set_status("PROCESSING...")
	_, reply = process_command(
	command,
	use_voice=True,
	history=conversation_history(),
		status_callback=set_status,
	)
	add_interaction(command, reply)
	set_status("READY")

if "messages" not in st.session_state:
	persisted = load_conversations()
	st.session_state.messages = []
	for item in persisted[-10:]:
		if item.get("user"):
			st.session_state.messages.append({"role": "user", "content": item["user"]})
		if item.get("jarvis"):
			st.session_state.messages.append({"role": "assistant", "content": item["jarvis"]})
	if not st.session_state.messages:
		st.session_state.messages = [{"role": "assistant", "content": "Hello. I am Jarvis. What shall we work on?"}]
if "status" not in st.session_state:
	st.session_state.status = "SYSTEM READY / GEMINI ACTIVE"

with st.sidebar:
	st.markdown("## JARVIS")
	st.caption("Personal AI Voice Assistant")
	st.divider()
	st.markdown("### QUICK ACTIONS")
	if st.button("🎙️ Start Voice Assistant", use_container_width=True):
		run_voice_command()
	if st.button("🌐 Open Chrome", use_container_width=True):
		run_text_command("open chrome")
	if st.button("🧮 Open Calculator", use_container_width=True):
		run_text_command("open calculator")
	if st.button("📖 Search Wikipedia", use_container_width=True):
		run_text_command("wikipedia artificial intelligence")
	st.divider()
	if st.button("Clear Conversation", use_container_width=True):
		clear_conversations()
		st.session_state.messages = []
		st.session_state.status = "SYSTEM READY / GEMINI ACTIVE"
		st.session_state.messages = [{"role": "assistant", "content": "Hello. I am Jarvis. What shall we work on?"}]
		st.rerun()

st.markdown(
	'<div class="hero"><div class="eyebrow">VOICE ASSISTANT / GEMINI ENABLED</div><h1>JARVIS</h1><p>Your personal AI assistant for voice commands, automation, research, and intelligent conversation.</p></div>',
	unsafe_allow_html=True,
)
status_box = st.empty()
st.session_state.status_box = status_box
status_box.markdown(f'<div class="status">● {st.session_state.status}</div>', unsafe_allow_html=True)

st.markdown('<div class="mic-panel"><div class="mic-label">VOICE CONTROL</div></div>', unsafe_allow_html=True)
if st.button("🎙️  Talk to JARVIS", use_container_width=True):
	run_voice_command()

for message in st.session_state.messages:
	with st.chat_message(message["role"]):
		st.markdown(message["content"])

if prompt := st.chat_input("Ask JARVIS anything..."):
	run_text_command(prompt)
