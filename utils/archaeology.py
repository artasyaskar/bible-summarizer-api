import json
import os

def get_archeological_proof(book: str, chapter: str) -> str | list[str] | dict:
    """
    Retrieves archaeological proof(s) for a given Bible book and chapter.
    The proof can be a string, a list of strings (multiple proofs), or a dictionary for more structured data.
    """
    # Normalize book name for consistency (e.g., "1 Kings" vs "1kings")
    normalized_book = book.lower().replace(" ", "").replace("1", "1st").replace("2", "2nd").replace("3", "3rd")
    
    # Ensure chapter is treated as a string, as it might come as an int from app.py
    chapter_str = str(chapter)

    # Key for chapter-specific proof
    specific_key = f"{normalized_book}_{chapter_str}"
    # Key for book-level general proof (fallback)
    general_book_key = normalized_book

    # Construct path relative to this file's directory for robustness
    # __file__ is utils/archaeology.py, so ../data/ goes to project_root/data/
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "..", "data", "archaeological_proofs.json")

    if not os.path.exists(path):
        # Log this error for server-side visibility (consider using a proper logger)
        print(f"CRITICAL: Archaeological data file not found at {path}")
        return {"error": "Archaeological data file is missing. Please contact administrator."}

    try:
        with open(path, "r", encoding="utf-8") as f: # Specify encoding
            data = json.load(f)
        
        # Try chapter-specific key first
        proof = data.get(specific_key)
        
        if proof is not None:
            return proof
        
        # Fallback to book-level general proof if chapter-specific one is not found
        general_proof = data.get(general_book_key)
        if general_proof is not None:
            return general_proof
            
        return "No specific archaeological proof found for this passage or book."

    except json.JSONDecodeError:
        print(f"ERROR: Failed to decode JSON from {path}")
        return {"error": "Archaeological data file is corrupted. Please contact administrator."}
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while fetching archaeological proof: {str(e)}")
        return {"error": "An error occurred while fetching archaeological proof. Please contact administrator."}
