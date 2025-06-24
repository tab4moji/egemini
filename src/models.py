#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module retrieves a comprehensive list of Gemini models via the
Google Generative Language API.

Revision History:
1.0.1 2025-06-23
  Program Purpose:
      Retrieve a list of Gemini models.
  Functionality:
      Calls the Gemini API and returns a list of available model names.
  Keywords:
      retrieve_gemini_models, requests, GEMINI_API_KEY, error_handling, single_return_statement
1.0.0 2025-06-22
  Program Purpose:
      Retrieve a list of Gemini models.
  Functionality:
      Calls the Gemini API and returns a list of available model names.
  Keywords:
      retrieve_gemini_models, requests, GEMINI_API_KEY
"""

import os
import sys

import requests


def retrieve_gemini_models():
    """
    Purpose: Retrieve a comprehensive list of available Gemini models via the
    Google Generative Language API.

    Detailed Operation:
    1. Attempts to retrieve the 'GEMINI_API_KEY' from environment variables
       if no API key is provided. 
    2. If the API key is absent, an empty list is returned after logging an error. 
    3. Constructs the API endpoint URL using the API key. 
    4. Makes an HTTP GET request to the Gemini API with a timeout. 
    5. Checks for HTTP errors and handles exceptions, printing errors to
       sys.stderr. 
    6. Parses the JSON response and extracts the 'name' of each model from the
       'models' array. 
    7. Returns the list of model names or an empty list if an error occurs. 

    Returns:
        list: A list of Gemini model names (strings) if successful, or an empty
        list if the API key is invalid or an error occurs. 
    """
    models = []

    # Other logic: API key retrieval
    api_key = os.getenv("GEMINI_API_KEY")

    # Core logic: Handle missing API key
    if not api_key:
        print("Error: GEMINI_API_KEY is not set. "
              "Please set the environment variable or pass it as an argument.",
              file=sys.stderr)
    else:
        # Other logic: Construct API endpoint
        base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        url = f"{base_url}?key={api_key}"

        # Core logic: API call and response processing
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors

            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
        except requests.exceptions.RequestException as error:
            print(
                f"An error occurred during the API call: {error}",
                file=sys.stderr
            )
        except KeyError as error:
            print(
                f"Error: Unexpected key not found during JSON response parsing: "
                f"{error}. Response might be malformed or API contract changed.",
                file=sys.stderr
            )

    return models


def main():
    """
    Main function to retrieve and display Gemini models. 
    It calls retrieve_gemini_models and prints the results or an error message. 
    """
    # NOTE: Do NOT hardcode your API key here.
    # Set GEMINI_API_KEY as an environment variable (e.g., in your shell profile)
    # export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    # or pass it directly to the function for testing purposes.

    gemini_models = retrieve_gemini_models()
    if gemini_models:
        print("Model List: (https://ai.google.dev/gemini-api/docs/models)")
        for model in gemini_models:
            print(f"- {model}")
    else:
        print("Failed to retrieve Gemini models. "
              "Check your API key and network connection.",
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
