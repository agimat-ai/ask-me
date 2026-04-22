import json
import time

from openai import OpenAI
from pypdf import PdfReader

from .config import (
    CHAT_MODEL,
    DEFAULT_NEGATIVE_CONFIDENCE_THRESHOLD,
    DEFAULT_SENTIMENT_PUSH_COOLDOWN_SECONDS,
    MAX_CONVERSATION_PREVIEW_CHARS,
    MAX_LATEST_MESSAGE_PREVIEW_CHARS,
    SENTIMENT_MODEL,
    SENTIMENT_NEGATIVE,
    SENTIMENT_NEUTRAL,
    SENTIMENT_SYSTEM_PROMPT,
    VALID_SENTIMENT_LABELS,
)
from .notifications import push
from .tooling import TOOLS, TOOL_REGISTRY


class Me:
    def __init__(self):
        self.openai = OpenAI()
        self.name = "Rene"
        self.last_sentiment_push_at = 0.0
        self.last_sentiment_label = None
        self.sentiment_push_cooldown_seconds = DEFAULT_SENTIMENT_PUSH_COOLDOWN_SECONDS
        self.sentiment_negative_confidence_threshold = DEFAULT_NEGATIVE_CONFIDENCE_THRESHOLD

        reader = PdfReader("me/linkedin.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = TOOL_REGISTRY.get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": tool_call.id,
                }
            )
        return results

    def system_prompt(self):
        system_prompt = (
            f"You are acting as {self.name}. You are answering questions on {self.name}'s website, "
            f"particularly questions related to {self.name}'s career, background, skills and experience. "
            f"Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. "
            f"You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. "
            "Be professional and engaging, as if talking to a potential client or future employer who came across the website. "
            "If you don't know the answer to any question, use your record_unknown_question tool to record the question that "
            "you couldn't answer, even if it's about something trivial or unrelated to career. "
            "If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their "
            "email and record it using your record_user_details tool. "
        )
        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt

    def chat(self, message, history):
        latest_user_message = message
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [
            {"role": "user", "content": latest_user_message}
        ]
        done = False
        while not done:
            response = self.openai.chat.completions.create(
                model=CHAT_MODEL,
                messages=messages,
                tools=TOOLS,
            )
            if response.choices[0].finish_reason == "tool_calls":
                assistant_message = response.choices[0].message
                tool_calls = assistant_message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(assistant_message)
                messages.extend(results)
            else:
                done = True

        full_conv = self.get_full_conversation_text(history, latest_user_message)
        #user_only_text = self.get_user_messages(history, latest_user_message)
        sentiment = self.analyze_user_sentiment(latest_user_message)
        print("User sentiment:", sentiment, flush=True)
        if self.is_acceptable_sentiment(sentiment):
            self.maybe_push_sentiment(sentiment, latest_user_message, full_conv)

        return response.choices[0].message.content

    def get_full_conversation_text(self, history, latest_user_message):
        lines = []
        for entry in history:
            role = entry.get("role", "unknown")
            content = entry.get("content", "")
            lines.append(f"{role}: {content}")
        lines.append(f"user: {latest_user_message}")
        return "\n".join(lines)

    def get_user_messages(self, history, latest_user_message):
        msgs = [entry.get("content", "") for entry in history if entry.get("role") == "user"]
        msgs.append(latest_user_message)
        return "\n".join(msgs)

    def analyze_user_sentiment(self, user_text):
        resp = self.openai.chat.completions.create(
            model=SENTIMENT_MODEL,
            messages=[
                {"role": "system", "content": SENTIMENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)

    def is_acceptable_sentiment(self, sentiment):
        if not isinstance(sentiment, dict):
            return False
        label = str(sentiment.get("sentiment", "")).lower().strip()
        if label not in VALID_SENTIMENT_LABELS:
            return False
        try:
            confidence = float(sentiment.get("confidence", 0))
        except (TypeError, ValueError):
            return False
        return 0.0 <= confidence <= 1.0

    def maybe_push_sentiment(self, sentiment, latest_user_message, full_conversation_text):
        label = str(sentiment.get("sentiment", SENTIMENT_NEUTRAL)).lower().strip()
        try:
            confidence = float(sentiment.get("confidence", 0))
        except (TypeError, ValueError):
            confidence = 0.0
        rationale = str(sentiment.get("rationale", "")).strip()

        if label != SENTIMENT_NEGATIVE or confidence < self.sentiment_negative_confidence_threshold:
            self.last_sentiment_label = label
            return

        now = time.time()
        in_cooldown = (now - self.last_sentiment_push_at) < self.sentiment_push_cooldown_seconds
        same_label_as_last = self.last_sentiment_label == label
        if in_cooldown and same_label_as_last:
            return

        snippet = latest_user_message.replace("\n", " ").strip()[:MAX_LATEST_MESSAGE_PREVIEW_CHARS]
        convo_preview = full_conversation_text.replace("\n", " ").strip()[:MAX_CONVERSATION_PREVIEW_CHARS]
        push(
            f"User sentiment alert: {SENTIMENT_NEGATIVE} "
            f"(confidence={confidence:.2f}). "
            f"Latest: {snippet or '[no user text]'} | "
            f"Reason: {rationale or '[none]'} | "
            f"Context: {convo_preview or '[no context]'}"
        )
        self.last_sentiment_push_at = now
        self.last_sentiment_label = label

