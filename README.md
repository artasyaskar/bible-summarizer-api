# Bible Summarizer API

[![Run on Replit](https://replit.com/badge/github/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME)](https://replit.com/github/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME) 
<!-- TODO: Replace YOUR_GITHUB_USERNAME/YOUR_REPO_NAME with the actual GitHub repo path after it's pushed -->

This API provides endpoints to fetch Bible verses from a specified book and chapter, generate a summary of those verses, and retrieve related archaeological proofs. It is configured for deployment on Replit.

## Features

*   Fetches Bible verses using the [bible-api.com](https://bible-api.com/) (KJV translation).
*   Summarizes the fetched verses using a Hugging Face Transformer model (`sshleifer/distilbart-cnn-12-6`).
*   Provides relevant archaeological information related to the Bible passage from a curated JSON dataset.
*   API documentation available via Swagger UI.

## API Documentation

Once the application is running (either locally or on Replit), the Swagger UI documentation can be accessed at `/api/docs/`.

The OpenAPI specification is available at `/static/swagger.yaml`.

### Endpoint: `POST /summarize`

Summarizes a Bible chapter and provides archaeological proof.

**Request Body:**

```json
{
  "book": "string",
  "chapter": "string"
}
```

*   `book` (string, required): The name of the Bible book (e.g., "Genesis", "John").
*   `chapter` (string, required): The chapter number (e.g., "3") or a chapter range (e.g., "3-5").

**Responses:**

*   `200 OK`: Successful response.
    ```json
    {
      "book": "John 3", // Reference to the book and chapter
      "verses": "For God so loved the world...",
      "summary": "A summary of the verses.",
      "archeological_proof": "The Pilate Stone..." // Can be string, list, or object
    }
    ```
*   `400 Bad Request`: Invalid input (e.g., missing parameters, invalid format).
    ```json
    {
      "error": "Book and Chapter are required"
    }
    ```
*   `404 Not Found`: Book or chapter not found by the Bible API or no verses text returned.
    ```json
    {
      "error": "Book or chapter not found: InvalidBook 999"
    }
    ```
*   `500 Internal Server Error`: Error during text summarization or other unexpected server-side issue.
    ```json
    {
      "error": "Error during text summarization"
    }
    ```
*   `503 Service Unavailable`: Error connecting to the external Bible API.
    ```json
    {
      "error": "Error connecting to Bible API: <details>"
    }
    ```

## Technology Stack

*   **Backend:** Python, Flask
*   **Text Summarization:** Hugging Face Transformers (`sshleifer/distilbart-cnn-12-6`)
*   **WSGI Server (Production/Replit):** Gunicorn
*   **API Documentation:** Swagger UI / OpenAPI 3.0
*   **Testing:** Pytest, Pytest-Mock
*   **Deployment:** Configured for [Replit](https://replit.com/)

## Development & Deployment on Replit

This project is configured for easy development and deployment on Replit.

1.  **Import to Replit:**
    *   You can import this project directly from GitHub into Replit. Use the "Run on Replit" badge above (once the GitHub repo URL is updated in the badge) or import manually via Replit's interface.
    *   Replit will automatically detect the `.replit` and `replit.nix` files to configure the environment.

2.  **Running on Replit:**
    *   Once imported, click the "Run" button at the top of the Replit interface.
    *   Replit will install dependencies from `requirements.txt` and then execute the `run` command specified in the `.replit` file (`gunicorn app:app ...`).
    *   A web view will open showing the live application. The URL will be in the format `https://<repl-name>.<your-replit-username>.repl.co`.
    *   The API documentation will be available at `https://<repl-name>.<your-replit-username>.repl.co/api/docs/`.

3.  **Dependencies:**
    *   Python packages are listed in `requirements.txt`. Replit's package manager will install these.
    *   System-level dependencies are managed by `replit.nix`. The current configuration uses Python 3.11.

4.  **Key Replit Configuration Files:**
    *   `.replit`: Defines the run command, language, and environment variables.
        *   **Run command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`
    *   `replit.nix`: Configures the Nix environment, specifying Python version and other system packages if needed.

## Local Development Setup (Optional)

If you wish to develop locally outside of Replit:

### Prerequisites

*   Python 3.11+ (Recommended, to match Replit environment)
*   `pip` (Python package installer)
*   Virtual environment tool (e.g., `venv`, `conda`) - Recommended

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd bible-summarizer-api
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # On Windows
    # venv\Scripts\activate
    # On macOS/Linux
    # source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `torch` can be a large download. If you encounter issues, you might need to install it separately or ensure you have a stable internet connection.*

### Running Locally

1.  **Start the Flask development server:**
    ```bash
    python app.py
    ```
    The API will typically be available at `http://127.0.0.1:5000/`.
    The API documentation will be at `http://127.0.0.1:5000/api/docs/`.

2.  **To run with Gunicorn locally (simulating production/Replit):**
    ```bash
    gunicorn app:app --bind 127.0.0.1:8000
    ```
    The API will be available at `http://127.0.0.1:8000/`.

### Running Tests

1.  Ensure all development dependencies are installed (including `pytest` and `pytest-mock`).
2.  From the root directory of the project, run:
    ```bash
    pytest
    ```
    Or, for more verbose output:
    ```bash
    pytest -v
    ```

## Archaeological Data

Archaeological proofs are stored in `data/archaeological_proofs.json`. This file can be updated with new findings or modifications to existing entries. The structure allows for:
*   Simple string proofs.
*   Lists of strings for multiple proofs.
*   Complex objects for more detailed/structured information.

Keys are generally in the format `bookname_chapter` (e.g., `genesis_1`, `1stkings_9`) or just `bookname` for general book-level proofs (e.g., `genesis_general`). Book names are normalized (lowercase, spaces removed, ordinals like "1st" used).

## Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature-name`).
3. Make your changes.
4. Write or update tests for your changes.
5. Ensure all tests pass (`pytest`).
6. Commit your changes (`git commit -m 'Add some feature'`).
7. Push to the branch (`git push origin feature/your-feature-name`).
8. Create a new Pull Request.

Please ensure your code adheres to good Python practices and that any new dependencies are added to `requirements.txt`.
