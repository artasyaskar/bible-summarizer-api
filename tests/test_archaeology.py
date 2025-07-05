import pytest
import json
from unittest.mock import patch, mock_open
from utils.archaeology import get_archeological_proof

# Sample data for mocking the JSON file
MOCK_PROOFS_DATA = {
  "genesis_1": "Proof for Genesis 1.",
  "genesis_1st_1": "This should not be hit if 'genesis_1' is used due to normalization.",
  "1stkings_9": "Proof for 1 Kings 9.",
  "john_3": ["Proof 1 for John 3.", "Proof 2 for John 3."],
  "mark_general": "General proof for Mark.", # This key should be 'mark' after normalization
  "mark": "This is general proof for Mark's book.",
  "luke_10-12": "Proof for Luke chapters 10-12.", # Example of a chapter range key
  "errorbook_1": {"type": "complex", "source": "source X", "text": "Complex proof for errorbook 1."}
}

# Helper to get mock JSON data as a string
def get_mock_json_string():
    return json.dumps(MOCK_PROOFS_DATA)

@patch('utils.archaeology.os.path.exists')
@patch('builtins.open', new_callable=mock_open) # Mock open globally for this test
def test_get_proof_specific_chapter_exists(mock_file_open, mock_path_exists):
    mock_path_exists.return_value = True # Simulate file exists
    mock_file_open.return_value.read.return_value = get_mock_json_string()

    book = "Genesis"
    chapter = "1"
    proof = get_archeological_proof(book, chapter)
    assert proof == MOCK_PROOFS_DATA["genesis_1"]
    # Check normalization: 'genesis_1' key should be used
    # The function normalizes book to "genesis" and chapter to "1", forming "genesis_1"

@patch('utils.archaeology.os.path.exists')
@patch('builtins.open', new_callable=mock_open)
def test_get_proof_book_normalization(mock_file_open, mock_path_exists):
    mock_path_exists.return_value = True
    mock_file_open.return_value.read.return_value = get_mock_json_string()
    
    # Test different book name variations that should normalize
    # e.g., "1 Kings", "1kings", "1st kings" should all become "1stkings"
    proof = get_archeological_proof("1 Kings", "9")
    assert proof == MOCK_PROOFS_DATA["1stkings_9"]
    proof = get_archeological_proof("1kings", "9")
    assert proof == MOCK_PROOFS_DATA["1stkings_9"]
    proof = get_archeological_proof("1st kings", "9") # with space
    assert proof == MOCK_PROOFS_DATA["1stkings_9"]


@patch('utils.archaeology.os.path.exists')
@patch('builtins.open', new_callable=mock_open)
def test_get_proof_list_of_proofs(mock_file_open, mock_path_exists):
    mock_path_exists.return_value = True
    mock_file_open.return_value.read.return_value = get_mock_json_string()

    proof = get_archeological_proof("John", "3")
    assert proof == MOCK_PROOFS_DATA["john_3"]
    assert isinstance(proof, list)
    assert len(proof) == 2

@patch('utils.archaeology.os.path.exists')
@patch('builtins.open', new_callable=mock_open)
def test_get_proof_complex_object(mock_file_open, mock_path_exists):
    mock_path_exists.return_value = True
    mock_file_open.return_value.read.return_value = get_mock_json_string()
    
    proof = get_archeological_proof("ErrorBook", "1") # Normalizes to "errorbook_1"
    assert proof == MOCK_PROOFS_DATA["errorbook_1"]
    assert isinstance(proof, dict)
    assert proof["type"] == "complex"

@patch('utils.archaeology.os.path.exists')
@patch('builtins.open', new_callable=mock_open)
def test_get_proof_chapter_specific_not_found_fallback_to_general_book(mock_file_open, mock_path_exists):
    mock_path_exists.return_value = True
    mock_file_open.return_value.read.return_value = get_mock_json_string()

    # "mark_5" is not in MOCK_PROOFS_DATA, but "mark" (general for Mark) is.
    # Book "Mark" normalizes to "mark".
    proof = get_archeological_proof("Mark", "5") # Should try "mark_5", then "mark"
    assert proof == MOCK_PROOFS_DATA["mark"]

@patch('utils.archaeology.os.path.exists')
@patch('builtins.open', new_callable=mock_open)
def test_get_proof_chapter_and_general_book_not_found(mock_file_open, mock_path_exists):
    mock_path_exists.return_value = True
    mock_file_open.return_value.read.return_value = get_mock_json_string()

    # "nonexistentbook_1" and "nonexistentbook" are not in MOCK_PROOFS_DATA
    proof = get_archeological_proof("NonExistentBook", "1")
    assert proof == "No specific archaeological proof found for this passage or book."

@patch('utils.archaeology.os.path.exists')
def test_get_proof_file_not_exists(mock_path_exists):
    mock_path_exists.return_value = False # Simulate file does not exist
    
    proof = get_archeological_proof("Genesis", "1")
    assert proof == {"error": "Archaeological data file is missing. Please contact administrator."}

@patch('utils.archaeology.os.path.exists')
@patch('builtins.open', new_callable=mock_open)
def test_get_proof_json_decode_error(mock_file_open, mock_path_exists):
    mock_path_exists.return_value = True
    mock_file_open.return_value.read.return_value = "this is not valid json" # Corrupted JSON
    
    proof = get_archeological_proof("Genesis", "1")
    assert proof == {"error": "Archaeological data file is corrupted. Please contact administrator."}

@patch('utils.archaeology.os.path.exists')
@patch('builtins.open', new_callable=mock_open)
def test_get_proof_unexpected_exception_during_open(mock_file_open, mock_path_exists):
    mock_path_exists.return_value = True
    mock_file_open.side_effect = Exception("Unexpected error during file open")

    proof = get_archeological_proof("Genesis", "1")
    assert proof == {"error": "An error occurred while fetching archaeological proof. Please contact administrator."}

@patch('utils.archaeology.os.path.exists')
@patch('builtins.open', new_callable=mock_open)
def test_get_proof_chapter_range_key(mock_file_open, mock_path_exists):
    # This tests if a key like "luke_10-12" can be successfully retrieved
    # if the input chapter is "10-12".
    mock_path_exists.return_value = True
    mock_file_open.return_value.read.return_value = get_mock_json_string()

    book = "Luke"
    chapter_range = "10-12" # This exact string needs to be the chapter part of the key
    proof = get_archeological_proof(book, chapter_range)
    # Key will be "luke_10-12"
    assert proof == MOCK_PROOFS_DATA["luke_10-12"]

# Test how chapter numbers (int) are handled vs strings for keys
@patch('utils.archaeology.os.path.exists')
@patch('builtins.open', new_callable=mock_open)
def test_get_proof_chapter_as_int_vs_string(mock_file_open, mock_path_exists):
    mock_path_exists.return_value = True
    # JSON keys are always strings. '1' vs 1.
    # The function converts chapter to str: chapter_str = str(chapter)
    # So, MOCK_PROOFS_DATA should use string chapter numbers in keys like "genesis_1".
    mock_file_open.return_value.read.return_value = json.dumps({
        "booka_1": "Proof for chapter 1 (string key)",
        "bookb_2": "Proof for chapter 2 (string key)" 
    })

    # Test with chapter as string
    proof_str = get_archeological_proof("BookA", "1")
    assert proof_str == "Proof for chapter 1 (string key)"

    # Test with chapter as int
    proof_int = get_archeological_proof("BookB", 2) # chapter=2 (int)
    assert proof_int == "Proof for chapter 2 (string key)"
    # This works because `str(2)` becomes "2", matching the key "bookb_2".
```
