# jarvis-ai-voice-assistant

## Deploy on Streamlit Community Cloud

1. Push this project to a GitHub repository.
2. Open [share.streamlit.io](https://share.streamlit.io) and create an app.
3. Select the repository and branch `main`.
4. Set **Main file path** to `web/app.py`.
5. Do not select `jarvis/app.py`; that file is the local microphone/desktop entrypoint,
   not the Streamlit web application.
6. In the app settings, add this secret:

```toml
GEMINI_API_KEY = "your-key-here"
```

The deployed app supports text chat and Wikipedia search. Windows microphone input,
text-to-speech, and desktop actions such as opening Chrome or Calculator are local
features and are unavailable in the cloud container.

For local development, activate the virtual environment and run:

```powershell
python -m streamlit run web/app.py
```
