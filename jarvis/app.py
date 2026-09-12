from .memory import save_conversation
from .speech import speak, listen
from .commands import process_command


def main():
    speak("Hello, I am Jarvis. How can I help you?")

    while True:
        command = listen()
        if not command:
            continue

        should_continue, reply = process_command(command)
        save_conversation(command, reply)

        if not should_continue:
            break


if __name__ == "__main__":
    main()