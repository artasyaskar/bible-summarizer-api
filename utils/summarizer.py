from transformers import pipeline, set_seed
import logging # For logging errors

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the summarization pipeline
# Using a specific revision for reproducibility, though this model is quite standard.
MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
try:
    summarizer_pipeline = pipeline("summarization", model=MODEL_NAME, tokenizer=MODEL_NAME)
    # Some models benefit from a seed for deterministic output if do_sample=True, but for do_sample=False it's less critical.
    # set_seed(42) # Uncomment if you plan to use do_sample=True and want consistent results
except Exception as e:
    logging.error(f"Failed to load summarization model '{MODEL_NAME}': {e}")
    # Fallback or raise critical error depending on desired application behavior
    summarizer_pipeline = None 

# Define max input length based on typical limits for models like BART.
# distilbart-cnn-12-6 has a max positional embedding of 1024.
MODEL_MAX_INPUT_LENGTH = 1024 
# Desired summary length constraints
SUMMARY_MAX_LENGTH = 150 # Increased slightly
SUMMARY_MIN_LENGTH = 40  # Increased slightly

def summarize_text(text: str) -> str:
    if summarizer_pipeline is None:
        logging.error("Summarization pipeline is not available.")
        return "Error: Text summarization service is currently unavailable."

    if not text or not isinstance(text, str):
        logging.warning("Summarize_text called with empty or invalid input.")
        return "Error: No text provided for summarization."

    try:
        # Simple chunking strategy for texts longer than model's max input length
        # This is a basic approach; more advanced methods involve overlapping chunks, recursive summarization, etc.
        
        # Tokenize to get actual token count - more accurate than char count for model limits
        # However, for simplicity here, we'll stick to character count as an approximation,
        # as direct tokenization before splitting adds complexity with the current pipeline usage.
        # A more robust solution would use tokenizer.encode to check token length.
        
        text_len = len(text) # Character length as a proxy

        if text_len > MODEL_MAX_INPUT_LENGTH:
            logging.info(f"Text length ({text_len} chars) exceeds model max input ({MODEL_MAX_INPUT_LENGTH} chars). Applying basic chunking.")
            
            # Heuristic: Split into chunks that are slightly less than the max model length to allow for summarization overhead.
            # This is a very naive splitting strategy (by character, not by sentence or token).
            # For better results, split along sentence boundaries.
            num_chunks = (text_len // (MODEL_MAX_INPUT_LENGTH - SUMMARY_MAX_LENGTH)) + 1
            chunk_size = text_len // num_chunks
            
            chunks = [text[i:i + chunk_size] for i in range(0, text_len, chunk_size)]
            
            summaries = []
            for i, chunk in enumerate(chunks):
                if not chunk.strip(): # Skip empty chunks
                    continue
                logging.info(f"Summarizing chunk {i+1}/{len(chunks)} (length: {len(chunk)} chars)")
                # Adjust summary length for chunks - make them shorter
                chunk_summary_max_length = max(SUMMARY_MIN_LENGTH, SUMMARY_MAX_LENGTH // len(chunks)) 
                chunk_summary_min_length = max(10, SUMMARY_MIN_LENGTH // len(chunks))

                # Ensure chunk is not too short for the min_length requirement of the summary
                if len(chunk) < chunk_summary_min_length * 2: # Heuristic
                    logging.warning(f"Chunk {i+1} is too short for meaningful summarization, using chunk as is.")
                    summaries.append(chunk)
                    continue

                summary_output = summarizer_pipeline(
                    chunk, 
                    max_length=chunk_summary_max_length, 
                    min_length=chunk_summary_min_length, 
                    do_sample=False,
                    truncation=True # Ensure input is truncated if it somehow still exceeds model limits
                )
                summaries.append(summary_output[0]['summary_text'])
            
            final_summary = " ".join(summaries)
            # If the combined summary is too long, summarize it again (recursive summarization)
            if len(final_summary) > SUMMARY_MAX_LENGTH * 1.5: # Heuristic factor
                 logging.info("Combined summary is too long, performing a second pass summarization.")
                 final_summary_output = summarizer_pipeline(
                    final_summary,
                    max_length=SUMMARY_MAX_LENGTH,
                    min_length=SUMMARY_MIN_LENGTH,
                    do_sample=False,
                    truncation=True
                 )
                 final_summary = final_summary_output[0]['summary_text']
            return final_summary

        else:
            # Text is within the direct processing limit
            summary_output = summarizer_pipeline(
                text, 
                max_length=SUMMARY_MAX_LENGTH, 
                min_length=SUMMARY_MIN_LENGTH, 
                do_sample=False,
                truncation=True # Good practice
            )
            return summary_output[0]['summary_text']

    except Exception as e:
        logging.error(f"Error during text summarization: {e}")
        # Potentially inspect 'e' for specific HuggingFace transformer errors
        return "Error: Could not summarize text due to an internal issue."
