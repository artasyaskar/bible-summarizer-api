from transformers import pipeline

# Use a small free model for summarization
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

def summarize_text(text: str) -> str:
    # Keep it short for free models — max length control
    if len(text) > 1024:
        text = text[:1024]
    summary = summarizer(text, max_length=130, min_length=30, do_sample=False)
    return summary[0]['summary_text']
