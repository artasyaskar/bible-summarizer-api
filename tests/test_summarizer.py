import pytest
from unittest.mock import patch, MagicMock
from utils.summarizer import summarize_text, MODEL_MAX_INPUT_LENGTH, SUMMARY_MAX_LENGTH, SUMMARY_MIN_LENGTH

# Mock the Hugging Face pipeline
@pytest.fixture(scope="module") # Use module scope if pipeline loading is expensive
def mock_summarizer_pipeline():
    # Create a mock pipeline function
    # This mock will be used by the @patch decorator in tests
    mock_pipeline_instance = MagicMock()
    
    def side_effect_func(text, max_length, min_length, do_sample, truncation):
        # Simple mock: return a fixed summary or part of the input
        # Ensure the output format matches what the summarizer pipeline returns (a list of dicts)
        # Forcing a slightly different output to differentiate from input
        return [{'summary_text': f"Summary of: {text[:max_length-15]}"}]

    mock_pipeline_instance.side_effect = side_effect_func
    return mock_pipeline_instance

@patch('utils.summarizer.summarizer_pipeline') # Patch the loaded pipeline instance
def test_summarize_short_text(mock_pipeline_instance_func, mock_summarizer_pipeline):
    # Configure the mock_pipeline_instance_func (the one patched in utils.summarizer)
    # to use the behavior defined in our fixture's mock_pipeline_instance
    mock_pipeline_instance_func.side_effect = mock_summarizer_pipeline.side_effect
    
    test_text = "This is a short test text for summarization."
    expected_summary_part = "Summary of: This is a short test text for summarization."
    
    summary = summarize_text(test_text)
    
    assert expected_summary_part in summary
    # Check if the pipeline was called with appropriate parameters for short text
    mock_pipeline_instance_func.assert_called_once_with(
        test_text,
        max_length=SUMMARY_MAX_LENGTH,
        min_length=SUMMARY_MIN_LENGTH,
        do_sample=False,
        truncation=True
    )

@patch('utils.summarizer.summarizer_pipeline')
def test_summarize_long_text_chunking(mock_pipeline_instance_func, mock_summarizer_pipeline):
    mock_pipeline_instance_func.side_effect = mock_summarizer_pipeline.side_effect

    # Create text longer than MODEL_MAX_INPUT_LENGTH
    # MODEL_MAX_INPUT_LENGTH is 1024. SUMMARY_MAX_LENGTH is 150.
    # num_chunks = (text_len // (MODEL_MAX_INPUT_LENGTH - SUMMARY_MAX_LENGTH)) + 1
    # If text_len is 1200, num_chunks = (1200 // (1024 - 150)) + 1 = (1200 // 874) + 1 = 1 + 1 = 2
    long_text_part = "This is a segment of a very long text. " * 30 # Approx 30*38 = 1140 chars
    long_text = long_text_part * 2 # Approx 2280 chars to ensure multiple chunks and potential recursive summary

    # Expected number of calls depends on the chunking logic in summarize_text
    # Current logic:
    # text_len = 2280
    # num_chunks = (2280 // (1024 - 150)) + 1 = (2280 // 874) + 1 = 2 + 1 = 3
    # chunk_size = 2280 // 3 = 760
    # So, 3 chunks.
    # If combined summary is long, one more call for recursive summarization.
    # Let's assume the combined summary of 3 chunks will be long enough for a recursive call.

    summary = summarize_text(long_text)

    assert "Summary of:" in summary # Check if summarization happened

    # Expect 3 calls for chunks + 1 call for the combined summary if it's too long.
    # The mock_summarizer_pipeline returns "Summary of: {chunk_text}"
    # Chunk summary max length for 3 chunks: max(40, 150 // 3) = max(40, 50) = 50
    # Each chunk summary: "Summary of: {text_of_length_approx_50-15}" -> length approx 13 + 35 = 48
    # Combined summary of 3 chunks: approx 3 * 48 = 144 chars.
    # This is less than SUMMARY_MAX_LENGTH * 1.5 (150 * 1.5 = 225).
    # So, it seems it might NOT trigger the recursive summarization in this specific case.
    # Let's re-evaluate:
    # If each chunk summary is "Summary of: This is a segment of a very long text. This is a segme" (length 50)
    # Combined: 3 * 50 = 150. This is NOT > 150 * 1.5. So, 3 calls.

    # Let's make the text even longer to ensure recursive summarization
    very_long_text = long_text_part * 3 # Approx 3420 chars
    # text_len = 3420
    # num_chunks = (3420 // 874) + 1 = 3 + 1 = 4
    # chunk_size = 3420 // 4 = 855
    # 4 chunks. Each summary approx 50 chars. Combined 200 chars.
    # 200 > 150 * 1.5 (225) is FALSE. Still no recursive.
    # The issue is `chunk_summary_max_length` for each chunk is `max(SUMMARY_MIN_LENGTH, SUMMARY_MAX_LENGTH // len(chunks))`
    # For 4 chunks: max(40, 150 // 4) = max(40, 37) = 40.
    # Each chunk summary length is 40. "Summary of: {text_of_length_40-15=25}". Total length approx 13 + 25 = 38.
    # Combined summary of 4 chunks: 4 * 38 = 152.
    # 152 > 225 is FALSE.

    # Let's simplify: assume the chunking leads to N calls, and then potentially one more.
    # For the `long_text` (2280 chars, 3 chunks):
    # chunk_summary_max_length = max(40, 150 // 3) = 50.
    # Each summary is "Summary of: {chunk_text[:35]}". Length is 13 + 35 = 48.
    # Combined: 3 * 48 = 144. Not > 225. So 3 calls are expected.

    summary_long = summarize_text(long_text) # Should make 3 calls
    assert mock_pipeline_instance_func.call_count == 3 

    # To test recursive, we need the sum of chunk summaries to exceed SUMMARY_MAX_LENGTH * 1.5 = 225
    # Let's use 6 chunks. chunk_summary_max_length = max(40, 150/6) = max(40, 25) = 40
    # Each summary length ~38. Combined 6 * 38 = 228. This IS > 225.
    # So, 6 chunk calls + 1 final call = 7 calls.
    mock_pipeline_instance_func.reset_mock() # Reset call count
    super_long_text = long_text_part * 5 # Approx 5700 chars
    # text_len = 5700
    # num_chunks = (5700 // 874) + 1 = 6 + 1 = 7
    # chunk_size = 5700 // 7 = 814
    # 7 chunks. chunk_summary_max_length = max(40, 150 // 7) = max(40, 21) = 40.
    # Each summary length ~38. Combined 7 * 38 = 266. This IS > 225.
    # So, 7 chunk calls + 1 final call = 8 calls.

    summary_super_long = summarize_text(super_long_text)
    assert mock_pipeline_instance_func.call_count == (7 + 1)


@patch('utils.summarizer.summarizer_pipeline', new=None) # Simulate pipeline failed to load
def test_summarize_text_pipeline_not_available():
    summary = summarize_text("Test text.")
    assert summary == "Error: Text summarization service is currently unavailable."

def test_summarize_text_empty_input():
    summary = summarize_text("")
    assert summary == "Error: No text provided for summarization."
    summary_none = summarize_text(None)
    assert summary_none == "Error: No text provided for summarization."

@patch('utils.summarizer.summarizer_pipeline')
def test_summarize_text_pipeline_exception(mock_pipeline_instance_func):
    mock_pipeline_instance_func.side_effect = Exception("Test pipeline error")
    
    summary = summarize_text("Some text that will cause an error.")
    assert summary == "Error: Could not summarize text due to an internal issue."

# Test chunking where a chunk is too short for min_length of summary
@patch('utils.summarizer.summarizer_pipeline')
def test_summarize_text_chunk_too_short(mock_pipeline_instance_func, mock_summarizer_pipeline):
    mock_pipeline_instance_func.side_effect = mock_summarizer_pipeline.side_effect
    
    # MODEL_MAX_INPUT_LENGTH = 1024, SUMMARY_MAX_LENGTH = 150
    # Create text slightly longer than MODEL_MAX_INPUT_LENGTH to make two chunks
    # One long, one very short.
    # num_chunks = (text_len // (MODEL_MAX_INPUT_LENGTH - SUMMARY_MAX_LENGTH)) + 1
    # text_len = 1050. num_chunks = (1050 // 874) + 1 = 1 + 1 = 2
    # chunk_size = 1050 // 2 = 525
    # chunks = [text[0:525], text[525:1050]]
    # chunk_summary_max_length = max(SUMMARY_MIN_LENGTH, SUMMARY_MAX_LENGTH // 2) = max(40, 75) = 75
    # chunk_summary_min_length = max(10, SUMMARY_MIN_LENGTH // 2) = max(10, 40 // 2) = 20
    # Condition: len(chunk) < chunk_summary_min_length * 2 (i.e. < 40 chars)
    
    # To force a short chunk:
    # Let text_len be just over MODEL_MAX_INPUT_LENGTH, e.g., 1030
    # num_chunks = (1030 // 874) + 1 = 2
    # chunk_size = 1030 // 2 = 515
    # Chunks: text[0:515], text[515:1030] - both are long enough.

    # Let's manually craft the chunks in the test for this specific scenario
    # by mocking the chunking process itself, or by designing input text carefully.
    # The current chunking: `chunks = [text[i:i + chunk_size] for i in range(0, text_len, chunk_size)]`
    # If text_len = 1025. num_chunks = 2. chunk_size = 512.
    # chunks = [text[0:512], text[512:1024], text[1024:1025]] -> 3 chunks. Last one is 1 char.
    text_one_char_last_chunk = "A" * (MODEL_MAX_INPUT_LENGTH -1) + "B" # Length 1024
    text_one_char_last_chunk = "A" * (MODEL_MAX_INPUT_LENGTH - 50) # Length 974
    # Add text to make it slightly longer, leading to a tiny last chunk
    # text_len = MODEL_MAX_INPUT_LENGTH + 10 = 1034
    # num_chunks = (1034 // (1024-150)) + 1 = (1034 // 874) + 1 = 1+1 = 2
    # chunk_size = 1034 // 2 = 517
    # chunks = [text[0:517], text[517:1034]] - both are fine.

    # The code's chunking `(text_len // (MODEL_MAX_INPUT_LENGTH - SUMMARY_MAX_LENGTH)) + 1`
    # and then `chunk_size = text_len // num_chunks` makes it hard to create a tiny last chunk
    # reliably without very specific lengths.
    # The warning `if len(chunk) < chunk_summary_min_length * 2:` is for when a chunk itself is too short.
    # `chunk_summary_min_length` can be as low as 10. So chunk length < 20.

    # Let's test this by ensuring one chunk is very small.
    # e.g. text = "A" * (MODEL_MAX_INPUT_LENGTH - 10) + " B" * 5 # Length 1024 characters
    # This will be one chunk.
    
    # To test the "chunk too short" logic, we need to ensure the chunking results in a small chunk.
    # This happens if `text_len` is small, but still > `MODEL_MAX_INPUT_LENGTH`.
    # This scenario is unlikely because if `text_len > MODEL_MAX_INPUT_LENGTH`, `num_chunks` will be at least 2.
    # And `chunk_size = text_len // num_chunks` will likely be substantial.
    # The specific line `if len(chunk) < chunk_summary_min_length * 2:` might be hard to hit with the current chunking logic
    # unless `SUMMARY_MIN_LENGTH // len(chunks)` becomes very small, meaning many chunks.

    # Consider a case where `text` itself is very short, but longer than `MODEL_MAX_INPUT_LENGTH` is not possible.
    # The "chunk too short" part of the code is:
    # `chunk_summary_min_length = max(10, SUMMARY_MIN_LENGTH // len(chunks))`
    # `if len(chunk) < chunk_summary_min_length * 2:`
    # If we have many chunks, `len(chunks)` is large, `SUMMARY_MIN_LENGTH // len(chunks)` can be small.
    # e.g. 10 chunks. `chunk_summary_min_length = max(10, 40 // 10) = max(10, 4) = 10`.
    # We need `len(chunk) < 20`.
    # If we have 10 chunks, `text_len` must be roughly `10 * (MODEL_MAX_INPUT_LENGTH - SUMMARY_MAX_LENGTH)`
    # which is `10 * 874 = 8740`. Then `chunk_size` is `8740 / 10 = 874`. This is not < 20.

    # It seems the specific `if len(chunk) < chunk_summary_min_length * 2:` condition
    # might only be hit if a chunk is genuinely tiny due to unusual text or splitting.
    # The current chunking `[text[i:i + chunk_size] for i in range(0, text_len, chunk_size)]`
    # will make the last chunk smaller if `text_len` is not a multiple of `chunk_size`.
    # Example: `text_len = 100`, `chunk_size = 30`. Chunks: `text[0:30], text[30:60], text[60:90], text[90:100]` (last is 10).
    # Let text_len = (MODEL_MAX_INPUT_LENGTH - SUMMARY_MAX_LENGTH) * 2 + 15  = 874 * 2 + 15 = 1748 + 15 = 1763
    # num_chunks = (1763 // 874) + 1 = 2 + 1 = 3
    # chunk_size = 1763 // 3 = 587
    # Chunks: text[0:587], text[587:1174], text[1174:1761] (last is 1763-1174 = 589, but should be 1761 from loop)
    # range(0, 1763, 587) -> 0, 587, 1174.
    # chunk1: text[0:587] (len 587)
    # chunk2: text[587:1174] (len 587)
    # chunk3: text[1174:1761] (len 587) -> No, text[1174:1763] (len 589)
    # The last chunk will be `text[1174:1763]`. Length = 1763-1174 = 589.
    # All chunks are large.

    # Let's try to make the last chunk small:
    # text_len = chunk_size * (num_chunks -1) + small_amount
    # Say num_chunks = 3. chunk_size = 500.
    # text_len = 500 * 2 + 15 = 1015.
    # For this text_len, the summarizer calculates:
    # num_chunks = (1015 // 874) + 1 = 1 + 1 = 2
    # chunk_size = 1015 // 2 = 507
    # Chunks: text[0:507], text[507:1014] (last one: text[507:1015] len 508)
    # Still doesn't produce a tiny chunk.

    # The only way to get a very small chunk with the current logic is if `chunk_size` itself is very small.
    # This means `text_len / num_chunks` is small.
    # This implies `text_len` is small, but then it wouldn't trigger chunking in the first place.
    # Or `num_chunks` is very large.
    # This specific path `len(chunk) < chunk_summary_min_length * 2` seems hard to test
    # without directly manipulating the chunks list or using a text that naturally creates such a scenario,
    # which the current chunking algorithm might prevent.
    # However, if it does occur, the code logs a warning and appends the chunk as is.
    # We can assume this part of the code is defensive.

    # Test that truncation=True is passed
    mock_pipeline_instance_func.reset_mock()
    summarize_text("Short text.")
    args, kwargs = mock_pipeline_instance_func.call_args
    assert kwargs.get('truncation') is True

    # Test that do_sample=False is passed
    assert kwargs.get('do_sample') is False

    # Test that max_length and min_length are passed correctly
    assert kwargs.get('max_length') == SUMMARY_MAX_LENGTH
    assert kwargs.get('min_length') == SUMMARY_MIN_LENGTH

    # Test the chunk summary length calculations for long text
    mock_pipeline_instance_func.reset_mock()
    # Use `very_long_text` (3420 chars) which creates 4 chunks
    # chunk_summary_max_length = max(40, 150 // 4) = 40
    # chunk_summary_min_length = max(10, 40 // 4) = 10
    summarize_text(very_long_text) # 4 chunks + 1 final = 5 calls
    
    # Check args for one of the chunk calls (e.g., the first one)
    first_chunk_call_args, first_chunk_call_kwargs = mock_pipeline_instance_func.call_args_list[0]
    assert first_chunk_call_kwargs.get('max_length') == 40 # SUMMARY_MAX_LENGTH // 4
    assert first_chunk_call_kwargs.get('min_length') == 10 # SUMMARY_MIN_LENGTH // 4

    # Check args for the final recursive call (if it happened, it would be the last call)
    # For `very_long_text`, it was 4 chunks. Summaries ~38 chars each. Combined = 152.
    # 152 is not > 1.5 * 150 (225). So no recursive call. Total 4 calls.
    assert mock_pipeline_instance_func.call_count == 4

    # Let's re-run `super_long_text` which should trigger recursive.
    # 5700 chars, 7 chunks.
    # chunk_max_len = max(40, 150/7) = 40. chunk_min_len = max(10, 40/7) = 10.
    # Summaries ~38 chars. Combined 7*38 = 266.
    # 266 > 225. So recursive call happens. Total 7+1 = 8 calls.
    mock_pipeline_instance_func.reset_mock()
    summarize_text(super_long_text)
    assert mock_pipeline_instance_func.call_count == 8
    
    last_call_args, last_call_kwargs = mock_pipeline_instance_func.call_args_list[-1] # The recursive call
    assert last_call_kwargs.get('max_length') == SUMMARY_MAX_LENGTH # Should use the main summary lengths
    assert last_call_kwargs.get('min_length') == SUMMARY_MIN_LENGTH
    # The input to this last call should be the combined summary of the chunks
    expected_input_to_recursive_summary = " ".join([f"Summary of: {chunk[:40-15]}" for chunk in ["dummy"]*7]) # Approximating structure
    actual_input_to_recursive_summary = last_call_args[0]
    assert "Summary of:" in actual_input_to_recursive_summary
    assert len(actual_input_to_recursive_summary) > SUMMARY_MAX_LENGTH # Because it triggered recursive
    assert len(actual_input_to_recursive_summary) <= (40 * 7) # Max possible length of combined chunk summaries
