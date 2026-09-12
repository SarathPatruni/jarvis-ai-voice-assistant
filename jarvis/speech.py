try:
    import speech_recognition as sr
except ImportError:  # pragma: no cover - optional runtime dependency
    sr = None

try:
    import pyttsx3
except ImportError:  # pragma: no cover - optional runtime dependency
    pyttsx3 = None


def speak(text):
    if pyttsx3 is None:
        print("Text-to-speech is unavailable because pyttsx3 is not installed.")
        return False
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.setProperty("volume", 1.0)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        return True
    except Exception as error:
        print("Text-to-speech error:", error)
        return False


def listen():
    if sr is None:
        print("Speech recognition is unavailable because SpeechRecognition is not installed.")
        return ""

    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("Listening...")
            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=10,
            )
    except sr.WaitTimeoutError:
        print("No speech detected.")
        return ""
    except (OSError, AttributeError) as error:
        print("Microphone unavailable:", error)
        return ""

    print("Processing...")

    try:
        text = recognizer.recognize_google(audio)
        print("You said:", text)
        return text

    except sr.UnknownValueError:
        print("Could not understand the audio.")
        speak("Sorry, I couldn't understand you.")
        return ""

    except sr.RequestError as e:
        print("Speech recognition service error:", e)
        speak("Sorry, I couldn't connect to the speech recognition service.")
        return ""

    except TimeoutError:
        print("Speech recognition request timed out.")
        speak("Sorry, the speech recognition service took too long to respond.")
        return ""
    except (OSError, AttributeError) as error:
        print("Microphone unavailable:", error)
        return ""