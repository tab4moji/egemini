Response Schema Mini Language Specification

## 1\. Overview

This document defines a **mini-language** for users to intuitively define complex JSON Schemas within a chat interface. In addition to traditional strict JSON notation, this first version features the following:

  - **Flexible Input Parsing**
    Allows a mix of quotation marks (double, single, or unquoted) for list expressions such as enums and arrays, enabling users to define them with greater freedom and fewer writing errors.

  - **Intuitive Notation**
    Leverages indentation and bullet symbols (`-`) to express hierarchical structures, arrays, and object definitions with a simple syntax.

## 2\. Purpose

  - To provide an environment where users can specify output formats using a simple notation close to natural language, without specialized JSON Schema knowledge.
  - To enable dynamic JSON Schema generation solely within chat schema blocks, without using command-line options or external files.
  - To achieve robust parsing against input variations by allowing flexibility, accommodating variations in quotation marks and notation.

## 3\. Syntax Rules

Schema definitions begin with a specific delimiter ( `::::` at the beginning of a line) within a chat message, followed by a schema block structured with indentation and newlines.

### 3.1 Top Level

  - Schema definition starts from the line immediately following `::::`.
  - The root JSON object is automatically generated, and definitions on each line are placed as properties under it.

### 3.2 Property Definition

  - **Basic Form**:

    ```
    KeyName: [Description]
    ```

    Here, "KeyName" becomes the property name in the output JSON, and the optional "Description" part is interpreted as `description`.
    Example:

    ```
    DishName: Name of the dish expressed humorously
    ```

    → In JSON, this is converted to `"DishName": { "type": "string", "description": "Name of the dish expressed humorously" }`.

  - **Type Inference**:
    If no type is explicitly specified in the syntax, it defaults to `string` type.

### 3.3 Enum Definition

  - **Basic Form**:

    ```
    KeyName: ["Value1", "Value2", ...]
    ```

    While conventionally all values were assumed to be enclosed in double quotes, this first version supports the following flexible format:

    ```
    Greeting: [ Konnichiwa, "hi, hello!", 'Konbanwa' ]
    ```

  - **About Flexible Parsing**:

      - Values can be written with double quotes, single quotes, or unquoted.
      - Internally, it first attempts parsing with standard `json.loads`. If it fails, a dedicated custom parser (e.g., `custom_parse_list`) splits the string within the square brackets by commas and removes extra spaces and quotes from the beginning and end of each value.
      - This automatically converts a description like:
        ```
        Greeting: [ Konnichiwa, "hi, hello!", 'Konbanwa' ]
        ```
        to:
        ```
        ["Konnichiwa", "hi, hello!", "Konbanwa"]
        ```
        correctly.

### 3.4 Array Definition

Arrays are primarily defined in two forms.

#### 3.4.1 Array of Objects

  - **Form**:
    ```
    ParentKey:
     - ChildKey1: [Description]
     - ChildKey2: [Description]
       ...
    ```
    This syntax is interpreted as the parent key being an array, and each of its elements being an object.
    Example:
    ```
    Ingredients:
     - IngredientName: Describe the raw material concretely
     - Quantity: Also specify the unit
    ```
    → In JSON Schema, this becomes `"Ingredients": { "type": "array", "items": { "type": "object", "properties": { "IngredientName": { "type": "string", "description": "Describe the raw material concretely" }, "Quantity": { "type": "string", "description": "Also specify the unit" } } } }`.

#### 3.4.2 Array of Strings

  - **Form**:
    ```
    ParentKey:
     - Text of list item 1
     - Text of list item 2
    ```
    In this case, each bullet item is interpreted as a string element.
    Example:
    ```
    CookingSteps:
     - First, gather the ingredients.
     - Cook while paying attention to the heat.
    ```
    → In JSON Schema, this is converted to `"CookingSteps": { "type": "array", "items": { "type": "string" } }`.

## 4\. JSON Schema Mapping Rules

Each element defined in this mini-language is converted to standard JSON Schema based on the following rules.

| Mini-language Element                  | JSON Schema Property                                                                |
| -------------------------------------- | ----------------------------------------------------------------------------------- |
| Root object                            | `{"type": "object", "properties": { ... }}`                                         |
| `KeyName: [Description]`               | `{"type": "string", "description": "Description"}`                                  |
| `KeyName: ["Value1", "Value2", ...]`   | `{"type": "string", "enum": ["Value1", "Value2", ...]}`                             |
| `ParentKey: <array of object>`         | `{"type": "array", "items": { "type": "object", "properties": { ... } }}`         |
| `ParentKey: <array of string>`         | `{"type": "array", "items": { "type": "string" }}`                                  |

## 5\. Error Handling and Implementation Notes

  - **Detection of Error States**

      - If there are syntax errors in the schema description (e.g., incorrect indentation, missing colons), the CLI tool outputs an appropriate error message and prompts the user to re-enter or continue without a schema.

  - **Infinite Loops and Deep Nesting**

      - Similar error handling and warnings are performed if excessive nesting or loops are detected, prompting the process to stop or for re-entry.

  - **Implementation of Flexible Input Processing**

      - In addition to processing with a standard JSON parser, a custom parser is used to supplement enum values, array elements, and other elements so that users can describe them in a flexible format.
      - This ensures robust parsing against input variations.

## 6\. Examples

### 6.1 Basic Example

**Input Example**:

```
::::
DishName: Name of the dish expressed humorously
Ingredients:
 - IngredientName: Describe the raw material concretely, avoiding ready-made mixes as much as possible
 - Quantity: Also specify the unit
CookingSteps:
 - First, gather the ingredients.
 - Cook while paying attention to the heat.
```

**Output Example**:

```json
{
  "type": "object",
  "properties": {
    "DishName": {
      "type": "string",
      "description": "Name of the dish expressed humorously"
    },
    "Ingredients": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "IngredientName": {
            "type": "string",
            "description": "Describe the raw material concretely, avoiding ready-made mixes as much as possible"
          },
          "Quantity": {
            "type": "string",
            "description": "Also specify the unit"
          }
        }
      }
    },
    "CookingSteps": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
```

### 6.2 Flexible Enum Example

**Input Example**:

```
::::
Greeting: [ Konnichiwa, "hi, hello!", 'Konbanwa' ]
```

**Output Example**:

```json
{
  "type": "object",
  "properties": {
    "Greeting": {
      "type": "string",
      "enum": ["Konnichiwa", "hi, hello!", "Konbanwa"]
    }
  }
}
```

## 7\. Future Extensibility

This initial version primarily implements the basic types currently supported (`string`, `array`, `object`, `enum`), but future extensions are planned, including:

  - Support for more diverse types such as `integer`, `boolean`, and `number`.
  - Implementation of additional properties like `required` constraints and `format` specifications.
  - Support for more complex nested structures and dynamic input processing.
