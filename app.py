import gradio as gr
from dotenv import load_dotenv

from chatbot_app import Me
from chatbot_app.config import INTRO_MESSAGE_TEMPLATE

if __name__ == "__main__":
    load_dotenv(override=True)
    me = Me()
    intro_message = INTRO_MESSAGE_TEMPLATE.format(name=me.name)
    chatbot = gr.Chatbot(
        type="messages",
        value=[{"role": "assistant", "content": intro_message}],
    )
    gr.ChatInterface(me.chat, type="messages", chatbot=chatbot).launch()
    