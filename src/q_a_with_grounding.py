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
2.3, 2025-06-24: Optimized streaming response handling in generate_response.
    - Merged the separate `decoded_chunk` assignment into a direct decode and append operation.
    - Reset `byte_stream_buffer` immediately after successful UTF-8 decoding.
    - Moved the reset of `json_fragment` outside the conditional block to streamline logic.
    - Simplified the conditional branching when appending to `json_buffer` for
      clearer JSON extraction.
2.4, 2025-06-24: Structured output with schema support.
    - Support for Structured Output**: The program can now extract a response schema from
      user input and use it to structure the model's output in JSON format.
    - Flexible Schema Definition Parsing**: New functionality has been added to parse
      schema blocks starting with `::::`, converting them flexibly into JSON Schema for enums,
      arrays of objects, and arrays of strings. This allows users to define output formats
      in a more natural language-like manner.
    - Custom Input Feature**: The introduction of the `custom_input` function,
      utilizing `prompt_toolkit`, provides a richer user input experience,
      including the ability to insert newlines with Alt+Enter.
    - Model Change**: The Gemini model used has been updated from `models/gemma-3n-e4b-it`
      to `models/gemini-2.0-flash`.
2.5, 2025-06-24: Added file attachment support.
    - Includes functionality to extract and process file attachments from user input.
    - Supported file types include various image, audio, and text formats.
    - Binary files (images, audio) are base64 encoded, and text files are read directly
      for inclusion in the request.
    - JSON files are specifically handled to be formatted as single-line strings.
    - The `get_model_response` function was updated to handle and include these attachments
      in the conversation history.
2.6, 2025-06-24: Added Google Search grounding capability.
    - Integrated `googleSearch` tool into the request body to enable real-time information
      retrieval during content generation.
    - Configured `tool_config` with `function_calling_config` mode set to `AUTO`
      for automatic tool invocation.

Keywords:
    GEMINI_MODEL, GEMINI_API_KEY, GEMINI_API_URL, generate_response, conversation_history,
    googleSearch, tool_config, AUTO.
"""

import os
import re
import sys
import json
import mimetypes
import base64
import requests

import prompt_toolkit

# Constants for the Gemini API (the model identifier is "gemma")
GEMINI_MODEL = "models/gemini-2.0-flash"
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

    request_body["tools"] = []
    request_body["tools"].append({ "googleSearch": {} })

    request_body["tool_config"] = {
        "function_calling_config": {
          "mode": "AUTO"
        }
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
                json_fragment += byte_stream_buffer.decode("utf-8")
            except UnicodeDecodeError:
                # Incomplete UTF-8 sequence; wait for the next chunk
                continue

            byte_stream_buffer = b""

            if json_buffer:
                json_buffer += json_fragment
            elif match := re.search(r"^[ \t\r\n]*data: (.+)$", json_fragment):
                json_buffer = match.group(1)
            else:
                continue

            json_fragment = ""

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
            user_text = custom_input(f"{role}: ")
        except EOFError:
            user_text = "It's OK, good bye."
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

    # user_record = {"role": "user", "parts": []}
    user_prompt = conversation_history[-1]
    generation_config = None
    if user_prompt["role"] == "user":
        user_attachments = []
        for part in user_prompt["parts"]:
            if "text" in part:
                if response_schema := extract_response_schema(part["text"]):
                    generation_config = {
                        "responseMimeType": "application/json",
                        "responseSchema": response_schema
                    }
                    break
        for part in user_prompt["parts"]:
            if "text" in part:
                result = extract_attachments(part["text"])
                user_attachments.append(result)
        user_prompt["parts"] += user_attachments

    response_text = ""
    for chunk in generate_response(conversation_history, generation_config):
        for candidate in chunk.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                text_chunk = part.get("text", "")
                if "{" in text_chunk and response_text == "":
                    print()
                print(text_chunk, end="", flush=True)
                response_text += part["text"]

    if re.search(r'}$', response_text):
        print()
    elif not re.search(r'\n$', response_text):
        print()

    return response_text.rstrip()


def extract_attachments(raw_text):
    """
    Extracts attachments from the user's raw input text and generates content objects
    (in dictionary format) for the Gemini API.
    If attachments are present, images or audio files are read in binary mode and
    encoded as a base64 string.

    Args:
        raw_text (str): The raw input text from the user (which may include attachment notations).

    Returns:
        list: A list of dictionaries containing attachment information.
    """
    # Helper function to process binary files (e.g., images or audio) in a unified manner.
    def _process_binary(filename):
        with open(filename, "rb") as binary_file:
            data = binary_file.read()
        encoded = base64.b64encode(data).decode("utf-8")
        return encoded

    # Helper function to read the contents of a text file.
    # If the file is JSON, it will be formatted as a single line.
    def _read_text_file(filename):
        try:
            with open(filename, "r", encoding="utf-8") as text_file:
                content = text_file.read()
        except UnicodeDecodeError:
            with open(filename, "rb") as text_file:
                content = text_file.read().decode("utf-8", errors="replace")
        if filename.lower().endswith(".json"):
            try:
                parsed = json.loads(content)
                content = json.dumps(parsed, separators=(',', ':'))
            except json.JSONDecodeError:
                pass
        return content

    block_pattern = r"\[\[(.+?)\]\]"
    filenames = re.findall(block_pattern, raw_text)
    extracted_attachments = []
    for filename in filenames:
        filename = os.path.expanduser(filename)
        if not os.path.isfile(filename):
            # Skip if the specified file is not found.
            print(f"file not found: {filename}", file=sys.stderr)
            continue
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type is None:
            continue
        if "json" in mime_type:
            # Gemini API does not support application/json, process as text/javascript instead.
            mime_type = "text/javascript"
        if "x-wav" in mime_type:
            # Gemini API does not support audio/x-wav, process as audio/wav instead.
            mime_type = "audio/wav"
        if "audio/mpeg" in mime_type:
            # Gemini API does not support audio/mpeg, process as audio/mp3 instead.
            mime_type = "audio/mp3"
        if "image/" in mime_type or "audio/" in mime_type:
            # Supported formats for the Gemini API (see API documentation for details)
            allowed_mime_types = [
                "image/png", "image/jpeg", "image/webp", "image/heic", "image/heif",
                "audio/wav", "audio/mp3", "audio/aiff", "audio/aac", "audio/ogg", "audio/flac"
            ]
            try:
                assert mime_type in allowed_mime_types
                content_data = _process_binary(filename)
                extracted_attachments.append({
                    "inline_data": {
                        "data": content_data,
                        "mime_type": mime_type
                    }
                })
            except AssertionError:
                print(f"unknown mime type: {mime_type} / {allowed_mime_types}", file=sys.stderr)
                continue
        else:
            try:
                allowed_text_types = [
                    "application/pdf",
                    "application/x-javascript", "text/javascript",
                    "application/x-python", "text/x-python",
                    "text/html", "text/css", "text/md", "text/csv", "text/xml", "text/rtf",
                    "text/plain"
                ]
                assert mime_type in allowed_text_types
                content_text = _read_text_file(filename)
                extracted_attachments.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": content_text
                    }
                })
            except AssertionError:
                print(f"unknown mime type: {mime_type} / {allowed_text_types}", file=sys.stderr)
                continue
    return extracted_attachments


def extract_response_schema(raw_text):
    """
    Extracts the "::::" block from the raw_text and converts it into a JSON Schema dictionary.
    """
    lines = raw_text.splitlines()
    schema_start = None
    for i, line in enumerate(lines):
        if line.strip() == "::::":
            schema_start = i + 1
            break
    if schema_start is None:
        return None
    schema_lines = [line.rstrip() for line in lines[schema_start:] if line.strip() != ""]
    props, _ = parse_properties(schema_lines, 0, 0)
    return {"type": "object", "properties": props}

def merge_object_schemas(schema_list):
    """
    Merge process: Merge multiple object schemas (dicts) into one.
    In case of duplicate keys, later occurrences override earlier ones.
    """
    merged = {"type": "object", "properties": {}}
    for schema in schema_list:
        if isinstance(schema, dict) and schema.get("type") == "object" and "properties" in schema:
            merged["properties"].update(schema["properties"])
    return merged

def custom_parse_list(text):
    """
    Custom parser: Splits the string inside square brackets [ ... ] by commas,
    trims whitespace and removes surrounding single or double quotes,
    and converts it into a list.
    Assumes that the input always begins with "[" and ends with "]".
    """
    inner = text[1:-1].strip()
    if not inner:
        return []
    tokens = []
    current_token = ""
    in_quote = False
    quote_char = ""
    escape = False
    for char in inner:
        if escape:
            current_token += char
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if in_quote:
            current_token += char
            if char == quote_char:
                in_quote = False
        else:
            if char in ['"', "'"]:
                in_quote = True
                quote_char = char
                current_token += char
            elif char == ",":
                tokens.append(current_token.strip())
                current_token = ""
            else:
                current_token += char
    if current_token:
        tokens.append(current_token.strip())
    result = []
    for token in tokens:
        is_token = token.startswith('"') and token.endswith('"')
        is_token = is_token or (token.startswith("'") and token.endswith("'"))
        if is_token:
            token = token[1:-1]
        result.append(token)
    return result

def parse_properties(lines, base_indent, start_index):
    """
    Parses properties at the specified indentation level.

    Properties are defined either as "key: [description]" or as "key:" followed by a child block.

    Returns:
      A tuple containing the properties dictionary and the next line index to process.
    """
    properties = {}
    line_index = start_index
    while line_index < len(lines):
        line = lines[line_index]
        indent = len(line) - len(line.lstrip(" "))
        if indent < base_indent:
            break
        # Do not treat bullet lines as properties
        if line.lstrip(" ").startswith("-"):
            break
        if ":" not in line.lstrip(" "):
            line_index += 1
            continue
        key, remainder = line.lstrip(" ").split(":", 1)
        key = key.strip()
        remainder = remainder.strip()
        definition = {}
        if remainder.startswith("[") and remainder.endswith("]"):
            try:
                enum_values = json.loads(remainder)
            except json.JSONDecodeError:
                enum_values = custom_parse_list(remainder)
            definition["type"] = "string"
            definition["enum"] = enum_values
        elif remainder != "":
            definition["type"] = "string"
            definition["description"] = remainder
        else:
            if line_index + 1 < len(lines):
                next_line = lines[line_index + 1]
                next_indent = len(next_line) - len(next_line.lstrip(" "))
                if next_line.lstrip().startswith("-") and next_indent > indent:
                    definition, new_index = parse_array_block(lines, line_index + 1, indent)
                    line_index = new_index - 1
                else:
                    definition["type"] = "string"
            else:
                definition["type"] = "string"
        properties[key] = definition
        line_index += 1
    return properties, line_index

def parse_array_block(lines, start_index, _parent_indent):
    """
    Parses an array block defined using bullet symbols.

    Returns:
      A tuple containing the JSON Schema for the array and the next line index to process.
    """
    if start_index >= len(lines):
        return {"type": "array", "items": {"type": "string"}}, start_index
    bullet_indent = len(lines[start_index]) - len(lines[start_index].lstrip(" "))
    items = []
    idx = start_index
    while idx < len(lines):
        current_line = lines[idx]
        current_indent = len(current_line) - len(current_line.lstrip(" "))
        if current_indent < bullet_indent or not current_line.lstrip().startswith("-"):
            break
        item, idx = parse_bullet_item(lines, idx, bullet_indent)
        items.append(item)
    # If all bullet items are objects, merge them into a single schema
    if items and all(isinstance(item, dict) for item in items):
        merged = merge_object_schemas(items)
        return {"type": "array", "items": merged}, idx

    return {"type": "array", "items": {"type": "string"}}, idx

def parse_bullet_item(lines, idx, bullet_indent):
    """
    Parses an array item that starts with a bullet symbol.

    If the item contains a colon, treat it as an object; if not, treat it as a string.

    Returns:
      A tuple containing the element's JSON Schema (or string) and the next line index to process.
    """
    line = lines[idx]
    content = line.lstrip()[1:].lstrip()
    bullet_lines = [" " * bullet_indent + content]
    idx += 1
    while idx < len(lines):
        next_line = lines[idx]
        next_indent = len(next_line) - len(next_line.lstrip(" "))
        if next_indent > bullet_indent:
            bullet_lines.append(next_line)
            idx += 1
        else:
            break
    if any(":" in line_item for line_item in bullet_lines):
        norm_lines = []
        min_indent = None
        for line_item in bullet_lines:
            current_indent = len(line_item.rstrip("\n")) - len(line_item.rstrip("\n").lstrip(" "))
            if min_indent is None or current_indent < min_indent:
                min_indent = current_indent
        for line_item in bullet_lines:
            norm_lines.append(line_item[min_indent:] if min_indent is not None else line_item)
        props, _ = parse_properties(norm_lines, 0, 0)
        value = {"type": "object", "properties": props}
    else:
        value = " ".join(line_item.strip() for line_item in bullet_lines)
    return value, idx


def custom_input(prompt_message=None):
    """
    Provides a custom input prompt with multiline mode support.

    Returns:
      The entered text.
    """

    def binding_handler_alt_enter(event):
        # Insert a newline when Alt+Enter is pressed.
        event.app.current_buffer.insert_text("\n")

    def binding_handler_ctrl_l(event):
        # Invalidate the current prompt to refresh the display.
        event.app.invalidate()

    def get_prompt_handler():
        if prompt_message is None:
            local_prompt = ""
        else:
            local_prompt = prompt_message
        return local_prompt

    key_bindings = prompt_toolkit.key_binding.KeyBindings()
    key_bindings.add("escape", "enter")(binding_handler_alt_enter)
    key_bindings.add("c-l")(binding_handler_ctrl_l)

    try:
        session = prompt_toolkit.PromptSession(key_bindings=key_bindings)
        input_text = session.prompt(get_prompt_handler, multiline=False)
    except KeyboardInterrupt as exc:
        raise EOFError from exc

    return input_text


def main():
    """
    Main function to interact with the Gemini API.
    It collects user input, records conversation history, and displays streaming responses.
    """
    conversation_history = []

    print(f"model: {GEMINI_MODEL}")
    print()
    print("You can insert a newline with ** Alt+Enter ** for your prompt.")
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
        if re.search(r'\b(?:bye|goodbye)\b', user_text, flags=re.IGNORECASE):
            break
    print()

    # End of main function


if __name__ == "__main__":  # Script entry point
    main()
