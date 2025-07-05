import pytest
import requests
from unittest.mock import patch, MagicMock # Changed from from unittest.mock import patch
from utils.bible import get_bible_verses

# Test successful API call
@patch('utils.bible.requests.get')
def test_get_bible_verses_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "reference": "John 3:16",
        "verses": [{"book_id": "JHN", "book_name": "John", "chapter": 3, "verse": 16, "text": "For God so loved the world..."}],
        "text": "For God so loved the world...",
        "translation_id": "kjv",
        "translation_name": "King James Version",
        "translation_note": "Public Domain"
    }
    mock_get.return_value = mock_response

    book = "John"
    chapter = "3"
    result = get_bible_verses(book, chapter)

    assert "error" not in result
    assert "text" in result
    assert result["text"] == "For God so loved the world..."
    mock_get.assert_called_once_with(f"https://bible-api.com/{book}%20{chapter}?translation=kjv")

# Test API call with invalid book/chapter (404 error)
@patch('utils.bible.requests.get')
def test_get_bible_verses_not_found(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    # bible-api.com might return a specific JSON error structure or just an HTML error page for 404s.
    # Let's assume it might return JSON like this, or the function handles non-200 generically.
    mock_response.json.return_value = {"error": "Book not found or chapter out of range."} 
    mock_get.return_value = mock_response

    book = "InvalidBook"
    chapter = "999"
    result = get_bible_verses(book, chapter)

    assert "error" in result
    # The function's current error message for non-200 is "Invalid book or chapter"
    assert result["error"] == "Invalid book or chapter" 
    mock_get.assert_called_once_with(f"https://bible-api.com/{book}%20{chapter}?translation=kjv")

# Test API call failure (e.g., network error)
@patch('utils.bible.requests.get')
def test_get_bible_verses_request_exception(mock_get):
    mock_get.side_effect = requests.exceptions.RequestException("Test network error")

    book = "Genesis"
    chapter = "1"
    
    # The function get_bible_verses is expected to raise this exception,
    # and app.py is expected to catch it.
    # So, we assert that the exception is raised here.
    with pytest.raises(requests.exceptions.RequestException):
        get_bible_verses(book, chapter)
    
    mock_get.assert_called_once_with(f"https://bible-api.com/{book}%20{chapter}?translation=kjv")

# Test API returning 200 but with an error message in JSON (if applicable for the API)
@patch('utils.bible.requests.get')
def test_get_bible_verses_success_with_internal_api_error_message(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200 # API itself is up
    mock_response.json.return_value = {"error": "Internal API error processing this book."} # But data has an error
    mock_get.return_value = mock_response

    book = "ErrorBook"
    chapter = "1"
    result = get_bible_verses(book, chapter)

    # Our function currently doesn't specifically look for "error" in a 200 response's JSON.
    # It expects verses. If "verses" is missing, it might lead to a KeyError or return empty text.
    # Based on current get_bible_verses:
    # verses = [verse["text"].strip() for verse in data.get("verses", [])]
    # return {"text": "\n".join(verses)}
    # If "verses" is not in data or is empty, result["text"] would be "".
    # This test reveals a potential improvement: check for data.get("error") even in 200 responses.
    # For now, testing current behavior:
    assert "error" not in result # The function itself doesn't return an "error" key for this case
    assert result["text"] == "" # Because "verses" would be missing from the mocked response
    mock_get.assert_called_once_with(f"https://bible-api.com/{book}%20{chapter}?translation=kjv")

# Test with chapter range (if bible-api.com supports it, e.g., "John 3:16-18")
# The current get_bible_verses function constructs URL like "Book%20Chapter"
# So "John%203:16-18" or "John%203-5".
# Let's assume bible-api.com handles "John%203-5" for whole chapters.
@patch('utils.bible.requests.get')
def test_get_bible_verses_chapter_range(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "reference": "John 3:1-5", # Example
        "verses": [
            {"text": "Verse 1..."},
            {"text": "Verse 2..."},
            {"text": "Verse 3..."},
            {"text": "Verse 4..."},
            {"text": "Verse 5..."}
        ],
        "text": "Verse 1...\nVerse 2...\nVerse 3...\nVerse 4...\nVerse 5..."
    }
    mock_get.return_value = mock_response

    book = "John"
    chapter_range = "3-5"
    result = get_bible_verses(book, chapter_range)

    assert "error" not in result
    assert result["text"] == "Verse 1...\nVerse 2...\nVerse 3...\nVerse 4...\nVerse 5..."
    mock_get.assert_called_once_with(f"https://bible-api.com/{book}%20{chapter_range}?translation=kjv")

# Test empty or malformed JSON response from API (status 200)
@patch('utils.bible.requests.get')
def test_get_bible_verses_malformed_json(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"unexpected_key": "some_data"} # Missing "verses"
    mock_get.return_value = mock_response

    book = "Genesis"
    chapter = "1"
    result = get_bible_verses(book, chapter)
    
    # Current behavior: returns empty string if "verses" is not found
    assert "error" not in result 
    assert result["text"] == ""
    mock_get.assert_called_once_with(f"https://bible-api.com/{book}%20{chapter}?translation=kjv")
    
@patch('utils.bible.requests.get')
def test_get_bible_verses_empty_verses_list(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"verses": []} # Empty list of verses
    mock_get.return_value = mock_response

    book = "Genesis"
    chapter = "1"
    result = get_bible_verses(book, chapter)
    
    assert "error" not in result 
    assert result["text"] == ""
    mock_get.assert_called_once_with(f"https://bible-api.com/{book}%20{chapter}?translation=kjv")
