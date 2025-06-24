# My Personal Gemini API Explorations

## Learning and Building: A Personal Journey with the Google Gemini API

This repository is a growing collection of my personal projects and experimental code, meticulously crafted as I **learn and build with** the powerful **Google Gemini API**. My aim is to explore the diverse capabilities of the **Gemini model** across a spectrum of innovative applications.

From advanced natural language processing to cutting-edge content generation, each endeavor within this repository is more than just code; it's a dedicated learning exercise, meticulously documenting my journey and discoveries with the Gemini API.

---

### Featured Explorations

This section highlights key projects and modules within this repository.

* **`models.py`**: This module is engineered to retrieve a comprehensive list of Gemini models directly from the Google Generative Language API.
    * [models.py](./src/models.py)
    * [Google AI for Developers/Gemini models](https://ai.google.dev/gemini-api/docs/models)

* **`q_a.py`**: An interactive Gemini API chatbot that streams real-time responses using custom UTF-8 decoding and environment-based API key retrieval.
    * [q_a.py](./src/q_a.py)
    * [Google AI for Developers/Streaming responses](https://ai.google.dev/gemini-api/docs/text-generation#rest_5)

* **`structed_q_a.py`**: An interactive Gemini API chatbot that supports structured output using a simple response schema (respMSL). This script provides a command-line interface for natural language interaction with the Gemini API, designed to easily parse structured responses for further processing.
    * [structed_q_a.py](./src/structed_q_a.py)
      ```plaintext
      user@penguin:src$ ./structed_q_a.py
      model: models/gemini-2.0-flash

      You can insert a newline with **Alt+Enter** for your prompt.
      user: hello.
      model: Hello! How can I help you today?
      user: What is the color of the Earth?
      ::::
      Earth’s colors: [green, blue, white]
      model:
      {
        "Earth’s colors": "green"
      }
      user: It's OK, good bye.
      model: Goodbye! Have a great day!

      user@penguin:src$
      ```
    * [simple response schema (respMSL)](./src/respsml_spec.md)
      ```plaintext
      What is the color of the Earth?
      ::::
      Earth’s colors: [green, blue, white]
      ```
    * [Google AI for Developers/Structured output](https://ai.google.dev/gemini-api/docs/structured-output#configuring-a-schema)

* **`q_a_with_files.py`**: An interactive Gemini API chatbot that supports file attachment and structured output using a simple response schema (respMSL).
    * [q_a_with_files.py](./src/q_a_with_files.py)
      ```plaintext
      user@penguin:src$ ./q_a_with_files.py
      model: models/gemini-2.0-flash

      You can insert a newline with ** Alt+Enter ** for your prompt.
      user:
      [[~/downloads/cat.jpg]]
      can you see it?
      ::::
      picture: [dog, cat, fish]
      model:
      {
        "picture": "cat"
      }
      user: [[~/downloads/speech.mp3]] Can you hear this ?
      model: Yes, I can hear the audio. It sounds like a person speaking about the importance of being able to communicate positions within a room in the context of production and staging.
      user: Transcribe what you just heard.
      model: Being able to communicate positions ...
      user:
      It's OK, good bye.
      model: Goodbye! Have a great day.

      user@penguin:src$
      ```
    * [simple response schema (respMSL)](./src/respsml_spec.md)
      ```plaintext
      [[~/downloads/cat.jpg]]
      Can you see it?
      ::::
      picture: [dog, cat, fish]
      ```
    * [Google AI for Developers/Structured output](https://ai.google.dev/gemini-api/docs/structured-output#configuring-a-schema)
    * [Google AI for Developers/Image understanding](https://ai.google.dev/gemini-api/docs/image-understanding#inline-image)
    * [Google AI for Developers/Audio understanding](https://ai.google.dev/gemini-api/docs/audio#inline-audio)

---

### Keywords

`Google Gemini API`, `Gemma 3n`, `LLM`, `Natural Language Processing`, `AI`, `Experimentation`, `Python`

---

### LICENSE

MIT license
