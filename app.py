from flask import Flask, request, jsonify
from utils.bible import get_bible_verses
from utils.summarizer import summarize_text
from utils.archaeology import get_archeological_proof

app = Flask(__name__)

@app.route("/summarize", methods=["POST"])
def summarize():
    data = request.json
    book = data.get("book")
    chapter = data.get("chapter")

    if not book or not chapter:
        return jsonify({"error": "Book and Chapter are required"}), 400

    verses = get_bible_verses(book, chapter)
    if "error" in verses:
        return jsonify(verses), 404

    full_text = verses["text"]
    summary = summarize_text(full_text)
    proof = get_archeological_proof(book, chapter)

    return jsonify({
        "verses": full_text,
        "summary": summary,
        "archeological_proof": proof
    })

if __name__ == "__main__":
    app.run(debug=True)
