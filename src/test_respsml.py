#!/usr/bin/env python3
"""
Update History:
1. 2025-06-24: Initial implementation. Converted schema blocks based on the mini-schema language
   specification into a JSON Schema.
2. 2025-06-24: Correction. Modified recursive processing for nested array properties and merged the
   parse_array_objects function.
3. 2025-06-24: Refactoring to address lint warnings and adhere to best practices.
4. 2025-06-24: Added flexible parsing to support mixed quoting.
5. 2025-06-24: Merged bullet items for object array definitions to ensure example1 and example2
   yield equivalent schema.
"""

import sys
import json
import prompt_toolkit

def extract_response_schema(text):
    """
    Extracts the "::::" block from the text and converts it into a JSON Schema dictionary.
    """
    lines = text.splitlines()
    schema_start = None
    for i, line in enumerate(lines):
        if line.strip() == "::::":
            schema_start = i + 1
            break
    if schema_start is None:
        print("Error: Schema block not found", file=sys.stderr)
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
        is_key = key.startswith('"') and key.endswith('"')
        is_key = is_key or (key.startswith("'") and key.endswith("'"))
        if is_key:
            key = key[1:-1]
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
    Provides a custom input prompt that supports multi-line mode.

    Returns:
      The text entered by the user.
    """
    def binding_handler_alt_enter(event):
        event.app.current_buffer.insert_text("\n")
    def binding_handler_ctrl_l(event):
        event.app.invalidate()
    def get_prompt_handler():
        return prompt_message if prompt_message is not None else ""
    key_bindings = prompt_toolkit.key_binding.KeyBindings()
    key_bindings.add("escape", "enter")(binding_handler_alt_enter)
    key_bindings.add("c-l")(binding_handler_ctrl_l)
    try:
        session = prompt_toolkit.PromptSession(key_bindings=key_bindings)
        input_text = session.prompt(get_prompt_handler, multiline=False)
    except KeyboardInterrupt:
        input_text = ""
    return input_text


def main():
    """
    Demonstrates schema extraction. Generates JSON Schema from sample text.
    """
    text = (
        "::::\n"
        "Dish Name: A quirky description of the dish\n"
        "Ingredients:\n"
        " - Ingredient: Instead of using ready-made mixes, list raw materials\n"
        "   Quantity: Include the unit\n"
        "Cooking Steps:\n"
        " - Used Ingredients:\n"
        "   Action: Also list the tools to be used\n"
    )
    schema = extract_response_schema(text)
    print("----")
    print(text)
    print("----")
    print(json.dumps(schema, ensure_ascii=False, indent=2))
    print("----")
    print()

    text = (
        "::::\n"
        "Recipe: a information about a food recipe.\n"
        "Ingredients:\n"
        " - Ingredient: a chiken\n"
        " - Quantity: 200g\n"
    )
    schema = extract_response_schema(text)
    print("----")
    print(text)
    print("----")
    print(json.dumps(schema, ensure_ascii=False, indent=2))
    print("----")
    print()

    text = (
        "::::\n"
        "Recipe: a information about a food recipe.\n"
        "Ingredients:\n"
        " - Ingredient: a chiken\n"
        "   Quantity: 200g\n"
    )
    schema = extract_response_schema(text)
    print("----")
    print(text)
    print("----")
    print(json.dumps(schema, ensure_ascii=False, indent=2))
    print("----")
    print()

    text = (
        "::::\n"
        "whether: [fine, cloud, rain]\n"
    )
    schema = extract_response_schema(text)
    print("----")
    print(text)
    print("----")
    print(json.dumps(schema, ensure_ascii=False, indent=2))
    print("----")
    print()

    print("You can insert a newline with ** Alt+Enter ** for your prompt.")
    text = custom_input("> ")
    schema = extract_response_schema(text)
    if schema is None:
        sys.exit(1)
    print(json.dumps(schema, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
