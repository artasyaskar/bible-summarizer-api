import requests

def get_bible_verses(book: str, chapter: str) -> dict:
    url = f"https://bible-api.com/{book}%20{chapter}?translation=kjv"
    response = requests.get(url)

    if response.status_code != 200:
        return {"error": "Invalid book or chapter"}

    data = response.json()
    verses = [verse["text"].strip() for verse in data.get("verses", [])]
    return {"text": "\n".join(verses)}
