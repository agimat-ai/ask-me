# Ask Me

A simple Gradio chat app that lets a persona ("Your Name") answer questions using profile context, call helper tools, and send Pushover notifications for specific events.

## Features

- Chat UI built with Gradio (`ChatInterface` + `Chatbot`)
- Persona-style responses backed by OpenAI chat completions
- Tool calling for:
  - recording user contact details
  - recording unknown/unanswered questions
- Basic user sentiment analysis per turn
- Pushover alerts for negative sentiment (with cooldown)

## Requirements

- Python 3.12
- OpenAI API key
- Optional but used by default: Pushover credentials 

Dependencies are listed in `requirements.txt`:

- `requests`
- `python-dotenv`
- `gradio`
- `pypdf`
- `openai`
- `openai-agents`

## Project Structure

- `app.py` - app entrypoint and Gradio UI wiring
- `chatbot_app/persona.py` - core chat, tool-calling, and sentiment flow
- `chatbot_app/tooling.py` - tool definitions and handlers
- `chatbot_app/notifications.py` - Pushover integration
- `chatbot_app/config.py` - app constants and model/config defaults
- `me/summary.txt` - persona summary context
- `me/linkedin.pdf` - LinkedIn/profile source used to build context at startup

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
PUSHOVER_TOKEN=your_pushover_app_token
PUSHOVER_USER=your_pushover_user_key
```

4. Make sure persona files exist:

- `me/summary.txt`
- `me/linkedin.pdf`

## Run

From the project root:

```bash
source .venv/bin/activate
python app.py
```

Or without activation:

```bash
./.venv/bin/python app.py
```

## Access the Chatbot

- After startup, Gradio prints a local URL in the terminal (usually `http://127.0.0.1:7860`).
- Open that URL in your browser to use the chatbot UI.
- If `7860` is already in use, Gradio may choose another port (check the printed URL).


## Notes

- `.python-version` is set to `3.12` and helps version managers pick the right Python.
- The app loads env vars via `python-dotenv` (`load_dotenv(override=True)`).

## Troubleshooting

- `ModuleNotFoundError: No module named 'gradio'`
  - You are likely running with a different Python than your virtual environment.
  - Use: `./.venv/bin/python app.py`

- `command not found: pip`
  - Use the interpreter form: `python -m pip install -r requirements.txt`
