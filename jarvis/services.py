import requests


def search_wikipedia(query):

    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + query.replace(" ", "_")

    headers = {
        "User-Agent": "JarvisVoiceAssistant/1.0"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        if response.status_code == 404:
            return "I couldn't find that topic on Wikipedia."

        response.raise_for_status()

        data = response.json()

        summary = data.get("extract")

        if not summary:
            return "I couldn't find a summary for that topic."

        return summary

    except requests.exceptions.RequestException as e:
        print("Wikipedia connection error:", e)
        return "I couldn't connect to Wikipedia right now."

    except Exception as e:
        print("Wikipedia error:", e)
        return "Something went wrong while searching Wikipedia."