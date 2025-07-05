import os
import requests # Import requests for requests.exceptions.RequestException
from flask import Flask, request, jsonify, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from utils.bible import get_bible_verses
from utils.summarizer import summarize_text
from utils.archaeology import get_archeological_proof

app = Flask(__name__)

# --- Swagger UI Setup ---
# Serve swagger.yaml from the root directory by creating a static folder for it implicitly
@app.route('/static/swagger.yaml')
def send_swagger_yaml():
    return send_from_directory('.', 'swagger.yaml')

SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
# Point API_URL to the new route that serves swagger.yaml
API_URL = '/static/swagger.yaml' 

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Bible Summarizer API"
    }
)
app.register_blueprint(swaggerui_blueprint)
# --- End Swagger UI Setup ---


@app.route("/summarize", methods=["POST"])
def summarize():
    data = request.json
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    book = data.get("book")
    chapter = data.get("chapter")

    if not book or not isinstance(book, str):
        return jsonify({"error": "Book is required and must be a string"}), 400
    if not chapter: # Chapter can be integer or string like "1-3"
        return jsonify({"error": "Chapter is required"}), 400
    
    # Basic validation for chapter format (e.g., integer or string like "1" or "1-3")
    # More sophisticated validation could be added (e.g. regex for specific bible book formats)
    try:
        if isinstance(chapter, int):
            if chapter <= 0:
                return jsonify({"error": "Chapter must be a positive integer"}), 400
        elif isinstance(chapter, str):
            if '-' in chapter:
                start_chap, end_chap = map(str.strip, chapter.split('-', 1))
                if not (start_chap.isdigit() and end_chap.isdigit() and int(start_chap) > 0 and int(end_chap) > 0 and int(start_chap) <= int(end_chap)):
                    return jsonify({"error": "Chapter range is invalid"}), 400
            elif not chapter.isdigit() or int(chapter) <= 0:
                 return jsonify({"error": "Chapter must be a positive integer or a valid range string like '1-3'"}), 400
        else:
            return jsonify({"error": "Chapter must be an integer or a string"}), 400

    except ValueError:
        return jsonify({"error": "Invalid chapter format"}), 400


    try:
        verses = get_bible_verses(book, str(chapter)) # Bible API expects chapter as string
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error connecting to Bible API: {str(e)}"}), 503 # Service Unavailable

    if "error" in verses:
        if "not found" in verses["error"].lower(): # Assuming bible-api.com returns specific error messages
            return jsonify({"error": f"Book or chapter not found: {book} {chapter}"}), 404
        return jsonify({"error": verses["error"]}), 400 # Other errors from bible API

    full_text = verses.get("text")
    if not full_text:
        # This case might occur if the API returns 200 but no verses (unlikely for valid book/chapter)
        return jsonify({"error": "No verses found for the specified book and chapter."}), 404

    try:
        summary = summarize_text(full_text)
    except Exception as e:
        # Log the exception e for debugging
        return jsonify({"error": "Error during text summarization"}), 500

    proof = get_archeological_proof(book, str(chapter)) # Ensure chapter is string for consistency

    return jsonify({
        "book": verses.get("reference", f"{book} {chapter}"), # Use reference from API if available
        "verses": full_text,
        "summary": summary,
        "archeological_proof": proof
    })

if __name__ == "__main__":
    # Consider using environment variables for host and port in production
    app.run(debug=False, host='0.0.0.0', port=os.environ.get('PORT', 5000))
