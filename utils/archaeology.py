import json
import os

def get_archeological_proof(book: str, chapter: str) -> str:
    path = os.path.join("data", "archaeological_proofs.json")
    try:
        with open(path, "r") as f:
            data = json.load(f)
        key = f"{book.lower()}_{chapter}"
        return data.get(key, "No archaeological proof found for this passage.")
    except:
        return "Archaeological data file missing or corrupted."
