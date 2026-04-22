import os

import requests

from .config import PUSHOVER_MESSAGES_URL


def push(text):
    requests.post(
        PUSHOVER_MESSAGES_URL,
        data={
            "token": os.getenv("PUSHOVER_TOKEN_LINKEDIN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        },
    )

