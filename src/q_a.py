#!/usr/bin/env python3
"""
Update History:
2.0, 2025-06-23: Reverted recent changes.
    - Restored GEMINI_MODEL identifier as "models/gemma-3n-e4b-it".
    - Reverted from using iter_lines to iter_content with manual UTF-8 decoding.
2.1, 2025-06-23: Refactored exception variable names, simplified UTF-8 decoding logic,
    and reduced nested blocks in generate_response.
2.2, 2025-06-23: Updated API key handling in stream_generate_content.
    - Now, if the api_key parameter is not provided, the function retrieves it from
      the environment variable "GEMINI_API_KEY".
Keywords:
    GEMINI_MODEL, GEMINI_API_KEY, GEMINI_API_URL, generate_response, conversation_history.
"""

import os
import re
import json
import requests


# Constants for the Gemini API (the model identifier is "gemma")
GEMINI_MODEL = "models/gemma-3n-e4b-it"
GEMINI_API_KEY = "GEMINI_API_KEY"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta"

def generate_response(conversation_history: dict, generation_config: dict = None):
    """
    Sends a streaming request to the Google AI Gemini API, handling UTF-8 decoding manually
    from iter_content to yield JSON-decoded response chunks.

    Args:
        conversation_history (dict): The conversation history.
        generation_config (dict, optional): The configuration dict for content generation.

    Yields:
        dict: A JSON-decoded chunk from the API response.
    """

    request_body = {
        "contents": conversation_history,
        "generationConfig": generation_config
    }

    byte_stream_buffer = b""
    json_fragment = ""
    json_buffer = ""

    # Other logic: API key retrieval
    api_key = os.getenv(GEMINI_API_KEY)

    try:
        response = requests.post(
            f"{GEMINI_API_URL}/{GEMINI_MODEL}:" "streamGenerateContent?alt=sse",
            headers= {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            },
            json=request_body,
            stream=True,
            timeout=(5, 10)
        )
        response.raise_for_status()

        for chunk in response.iter_content():

            if not chunk:
                continue

            byte_stream_buffer += chunk

            try:
                # Attempt to decode the accumulated bytes as UTF-8 and append to json_fragment
                decoded_chunk = byte_stream_buffer.decode("utf-8")
                json_fragment += decoded_chunk
                byte_stream_buffer = b""
            except UnicodeDecodeError:
                # Incomplete UTF-8 sequence; wait for the next chunk
                continue

            if json_buffer:
                json_buffer += json_fragment
                json_fragment = ""
            else:

                if match := re.search(r"^[ \t\r\n]*data: (.+)$", json_fragment):
                    json_buffer = match.group(1)
                    json_fragment = ""
                else:
                    continue

            try:
                parsed_data = json.loads(json_buffer)
                json_buffer = ""
            except json.JSONDecodeError:
                # The JSON data is incomplete; wait for more data
                continue

            if isinstance(parsed_data, list):
                for item in parsed_data:
                    yield item
            else:
                yield parsed_data

    except (
        requests.exceptions.HTTPError,
        requests.exceptions.ConnectionError,
        requests.exceptions.RequestException,
        requests.exceptions.Timeout) as request_error:
        yield {"error": "request_error", "message": str(request_error)}

    # End of generate_response function


def get_user_input(role):
    """
    Args:
        role (str): User role string (e.g. "user").

    return:
        str: The user's input.
    """

    while True:
        try:
            user_text = input(f"{role}: ")
        except EOFError:
            user_text = "bye."
            print(user_text)
        if user_text:
            break
    return user_text


def get_model_response(conversation_history):
    """
    Args:
        conversation_history (dict): Recorded conversation history including user prompts.

    return:
        str: The model's response message.
    """

    response_text = ""
    for chunk in generate_response(conversation_history):
        for candidate in chunk.get("candidates", []):
            if "finishReason" in candidate:
                continue
            if "parts" in candidate.get("content", {}):
                for part in candidate["content"]["parts"]:
                    if "text" in part and part["text"]:
                        print(part["text"], end="", flush=True)
                        response_text += part["text"]
    return response_text


def main():
    """
    Main function to interact with the Gemini API.
    It collects user input, records conversation history, and displays streaming responses.
    """
    conversation_history = []

    while True:
        user_record = {"role": "user", "parts": []}
        role = user_record["role"]
        user_text = get_user_input(role)
        user_record["parts"].append({"text": user_text})
        conversation_history.append(user_record)
        if user_text.lower() in ["exit", "quit"]:
            break

        model_record = {"role": "model", "parts": []}
        print("model: ", end="", flush=True)
        model_text = get_model_response(conversation_history)
        model_record["parts"].append({"text": model_text})
        if re.search(r'\b(?:bye|goodbye)\b', model_text, flags=re.IGNORECASE):
            break

    # End of main function


if __name__ == "__main__":  # Script entry point
    main()
