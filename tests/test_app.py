import pytest
import json
from app import app as flask_app # Import the flask app instance
from unittest.mock import patch, MagicMock

# Fixture to create a test client for the Flask app
@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    # Propagate exceptions from the app to the test client
    flask_app.config['PROPAGATE_EXCEPTIONS'] = True 
    with flask_app.test_client() as client:
        yield client

# Mock data and services
MOCK_BIBLE_VERSES_SUCCESS = {"text": "Mocked Bible verses for John 3."}
MOCK_BIBLE_VERSES_NOT_FOUND = {"error": "Book or chapter not found"}
MOCK_SUMMARY_SUCCESS = "Mocked summary of the verses."
MOCK_ARCHAEOLOGICAL_PROOF_SUCCESS = "Mocked archaeological proof for John 3."
MOCK_ARCHAEOLOGICAL_PROOF_LIST = ["Proof A", "Proof B"]
MOCK_ARCHAEOLOGICAL_PROOF_DICT = {"detail": "Complex proof"}
MOCK_ARCHAEOLOGICAL_PROOF_NOT_FOUND = "No archaeological proof found for this passage."

# --- Test /summarize endpoint ---

@patch('app.get_bible_verses')
@patch('app.summarize_text')
@patch('app.get_archeological_proof')
def test_summarize_success(mock_get_proof, mock_summarize, mock_get_verses, client):
    mock_get_verses.return_value = MOCK_BIBLE_VERSES_SUCCESS
    mock_summarize.return_value = MOCK_SUMMARY_SUCCESS
    mock_get_proof.return_value = MOCK_ARCHAEOLOGICAL_PROOF_SUCCESS

    response = client.post('/summarize', json={"book": "John", "chapter": "3"})
    data = response.get_json()

    assert response.status_code == 200
    assert data["verses"] == MOCK_BIBLE_VERSES_SUCCESS["text"]
    assert data["summary"] == MOCK_SUMMARY_SUCCESS
    assert data["archeological_proof"] == MOCK_ARCHAEOLOGICAL_PROOF_SUCCESS
    assert "book" in data # Check if book reference is included

    mock_get_verses.assert_called_once_with("John", "3")
    mock_summarize.assert_called_once_with(MOCK_BIBLE_VERSES_SUCCESS["text"])
    mock_get_proof.assert_called_once_with("John", "3")

@patch('app.get_bible_verses')
@patch('app.summarize_text')
@patch('app.get_archeological_proof')
def test_summarize_success_different_proof_types(mock_get_proof, mock_summarize, mock_get_verses, client):
    mock_get_verses.return_value = MOCK_BIBLE_VERSES_SUCCESS
    mock_summarize.return_value = MOCK_SUMMARY_SUCCESS

    # Test with list proof
    mock_get_proof.return_value = MOCK_ARCHAEOLOGICAL_PROOF_LIST
    response_list = client.post('/summarize', json={"book": "John", "chapter": "3"})
    data_list = response_list.get_json()
    assert response_list.status_code == 200
    assert data_list["archeological_proof"] == MOCK_ARCHAEOLOGICAL_PROOF_LIST

    # Test with dict proof
    mock_get_proof.return_value = MOCK_ARCHAEOLOGICAL_PROOF_DICT
    response_dict = client.post('/summarize', json={"book": "John", "chapter": "3"})
    data_dict = response_dict.get_json()
    assert response_dict.status_code == 200
    assert data_dict["archeological_proof"] == MOCK_ARCHAEological_PROOF_DICT


def test_summarize_missing_book(client):
    response = client.post('/summarize', json={"chapter": "3"})
    data = response.get_json()
    assert response.status_code == 400
    assert "error" in data
    assert data["error"] == "Book is required and must be a string"

def test_summarize_missing_chapter(client):
    response = client.post('/summarize', json={"book": "Genesis"})
    data = response.get_json()
    assert response.status_code == 400
    assert "error" in data
    assert data["error"] == "Chapter is required"

def test_summarize_invalid_book_type(client):
    response = client.post('/summarize', json={"book": 123, "chapter": "1"})
    data = response.get_json()
    assert response.status_code == 400
    assert data["error"] == "Book is required and must be a string"

def test_summarize_invalid_chapter_type(client):
    # The app.py validation allows int or str for chapter, but checks format
    # This test is for chapter being neither string nor int (e.g. list)
    response = client.post('/summarize', json={"book": "Genesis", "chapter": [1]})
    data = response.get_json()
    assert response.status_code == 400
    assert data["error"] == "Chapter must be an integer or a string"

def test_summarize_invalid_chapter_format_negative_int(client):
    response = client.post('/summarize', json={"book": "Genesis", "chapter": -1})
    data = response.get_json()
    assert response.status_code == 400
    assert data["error"] == "Chapter must be a positive integer"

def test_summarize_invalid_chapter_format_zero_int(client):
    response = client.post('/summarize', json={"book": "Genesis", "chapter": 0})
    data = response.get_json()
    assert response.status_code == 400
    assert data["error"] == "Chapter must be a positive integer"
    
def test_summarize_invalid_chapter_format_non_numeric_string(client):
    response = client.post('/summarize', json={"book": "Genesis", "chapter": "abc"})
    data = response.get_json()
    assert response.status_code == 400
    assert data["error"] == "Chapter must be a positive integer or a valid range string like '1-3'"

def test_summarize_invalid_chapter_range_format(client):
    response = client.post('/summarize', json={"book": "Genesis", "chapter": "1-abc"})
    data = response.get_json()
    assert response.status_code == 400
    assert data["error"] == "Chapter range is invalid"

    response = client.post('/summarize', json={"book": "Genesis", "chapter": "3-1"}) # end < start
    data = response.get_json()
    assert response.status_code == 400
    assert data["error"] == "Chapter range is invalid"

def test_summarize_valid_chapter_range_format(client, mocker): # Use mocker from pytest-mock
    # This test will actually call the downstream services if not mocked at app level
    mocker.patch('app.get_bible_verses', return_value=MOCK_BIBLE_VERSES_SUCCESS)
    mocker.patch('app.summarize_text', return_value=MOCK_SUMMARY_SUCCESS)
    mocker.patch('app.get_archeological_proof', return_value=MOCK_ARCHAEOLOGICAL_PROOF_SUCCESS)
    
    response = client.post('/summarize', json={"book": "Genesis", "chapter": "1-3"})
    assert response.status_code == 200 # Assuming downstream mocks handle it

def test_summarize_not_json(client):
    response = client.post('/summarize', data="this is not json")
    data = response.get_json()
    assert response.status_code == 400
    assert "error" in data
    assert data["error"] == "Request body must be JSON"


@patch('app.get_bible_verses')
def test_summarize_bible_api_not_found(mock_get_verses, client):
    mock_get_verses.return_value = MOCK_BIBLE_VERSES_NOT_FOUND
    
    response = client.post('/summarize', json={"book": "InvalidBook", "chapter": "999"})
    data = response.get_json()
    
    assert response.status_code == 404 # This is what app.py returns
    assert "error" in data
    assert "Book or chapter not found" in data["error"] # Check specific error from app.py
    mock_get_verses.assert_called_once_with("InvalidBook", "999")

@patch('app.get_bible_verses')
def test_summarize_bible_api_other_error(mock_get_verses, client):
    mock_get_verses.return_value = {"error": "Some other API error"}
    
    response = client.post('/summarize', json={"book": "ErrorBook", "chapter": "1"})
    data = response.get_json()
    
    assert response.status_code == 400 # Generic error from bible API
    assert "error" in data
    assert data["error"] == "Some other API error"

@patch('app.get_bible_verses')
def test_summarize_bible_api_connection_error(mock_get_verses, client):
    # Import requests directly here for the exception, or ensure app.py imports it for the except block
    import requests # Make sure this is available for raising the exception
    mock_get_verses.side_effect = requests.exceptions.RequestException("Network error")
    
    response = client.post('/summarize', json={"book": "Genesis", "chapter": "1"})
    data = response.get_json()
    
    assert response.status_code == 503 # Service Unavailable
    assert "error" in data
    assert "Error connecting to Bible API" in data["error"]

@patch('app.get_bible_verses', return_value=MOCK_BIBLE_VERSES_SUCCESS) # Success from Bible
@patch('app.summarize_text') # Mock summarizer
def test_summarize_summarizer_error(mock_summarize, mock_get_verses, client):
    mock_summarize.side_effect = Exception("Summarizer internal error")
    # We could also make summarize_text return its specific error string:
    # mock_summarize.return_value = "Error: Could not summarize text due to an internal issue."
    
    response = client.post('/summarize', json={"book": "John", "chapter": "3"})
    data = response.get_json()
    
    assert response.status_code == 500 # Internal Server Error
    assert "error" in data
    assert data["error"] == "Error during text summarization"
    mock_summarize.assert_called_once_with(MOCK_BIBLE_VERSES_SUCCESS["text"])

@patch('app.get_bible_verses', return_value={"text": None}) # API returns 200 but no text
@patch('app.summarize_text')
@patch('app.get_archeological_proof')
def test_summarize_no_verses_text_returned(mock_get_proof, mock_summarize, mock_get_verses, client):
    response = client.post('/summarize', json={"book": "John", "chapter": "3"})
    data = response.get_json()

    assert response.status_code == 404
    assert "error" in data
    assert data["error"] == "No verses found for the specified book and chapter."
    mock_summarize.assert_not_called() # Summarizer should not be called if no text
    mock_get_proof.assert_not_called() # Archaeology should not be called either


# --- Test Swagger UI endpoint ---
def test_swagger_ui_docs(client):
    response = client.get('/api/docs/') # Note the trailing slash for Flask-Swagger-UI
    assert response.status_code == 200
    assert b"Swagger UI" in response.data # Check for a known string in the Swagger UI page

def test_swagger_yaml_served(client):
    response = client.get('/static/swagger.yaml')
    assert response.status_code == 200
    # Check if it's YAML content, e.g. by checking for "openapi: 3.0.0"
    assert b"openapi: 3.0.0" in response.data
```
