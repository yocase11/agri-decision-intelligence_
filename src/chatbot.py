import requests
import json
from typing import List, Dict

import requests
import json
from typing import List, Dict
import os

class AgriChatbot:
    def __init__(self, api_url: str = "http://192.168.31.36:1234", model: str = "llama-3.2-3b-instruct", use_trained_model: bool = False):
        self.api_url = api_url
        self.model = model
        self.use_trained_model = use_trained_model
        self.conversation_history: List[Dict] = [
            {
                "role": "system",
                "content": "You are AgriChat, an AI assistant specialized in agriculture, farming, crop management, and agricultural economics. You help farmers with advice on crops, weather, pricing, and sustainable farming practices. You have access to agricultural knowledge and can provide helpful, practical advice."
            }
        ]

        # Initialize trained model if requested
        self.trained_chatbot = None
        if use_trained_model:
            try:
                from trained_agri_chatbot import get_agri_chatbot
                self.trained_chatbot = get_agri_chatbot()
                print("Using trained agricultural model for responses.")
            except ImportError:
                print("Trained model not available, falling back to API.")
                self.use_trained_model = False

    def chat(self, user_message: str) -> str:
        # Try trained model first if available
        if self.use_trained_model and self.trained_chatbot:
            try:
                return self.trained_chatbot.chat(user_message)
            except Exception as e:
                print(f"Trained model error: {e}, falling back to API")
                self.use_trained_model = False

        # Fallback to API
        return self._chat_with_api(user_message)

    def _chat_with_api(self, user_message: str) -> str:
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_message})

        # Prepare the payload for the API
        payload = {
            "model": self.model,
            "messages": self.conversation_history,
            "temperature": 0.7,
            "max_tokens": 500
        }

        try:
            response = requests.post(f"{self.api_url}/v1/chat/completions", json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()

            # Extract the assistant's response
            assistant_message = result["choices"][0]["message"]["content"]

            # Add assistant response to history
            self.conversation_history.append({"role": "assistant", "content": assistant_message})

            return assistant_message

        except requests.exceptions.RequestException as e:
            return f"Error communicating with API: {str(e)}"
        except (KeyError, IndexError) as e:
            return f"Error parsing API response: {str(e)}"

    def reset_conversation(self):
        self.conversation_history = [
            {
                "role": "system",
                "content": "You are AgriChat, an AI assistant specialized in agriculture, farming, crop management, and agricultural economics. You help farmers with advice on crops, weather, pricing, and sustainable farming practices. You have access to agricultural knowledge and can provide helpful, practical advice."
            }
        ]
        if self.trained_chatbot:
            self.trained_chatbot.reset_conversation()

    def chat(self, user_message: str) -> str:
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_message})

        # Prepare the payload for the API
        payload = {
            "model": self.model,
            "messages": self.conversation_history,
            "temperature": 0.7,
            "max_tokens": 500
        }

        try:
            response = requests.post(f"{self.api_url}/v1/chat/completions", json=payload)
            response.raise_for_status()
            result = response.json()

            # Extract the assistant's response
            assistant_message = result["choices"][0]["message"]["content"]

            # Add assistant response to history
            self.conversation_history.append({"role": "assistant", "content": assistant_message})

            return assistant_message

        except requests.exceptions.RequestException as e:
            return f"Error communicating with API: {str(e)}"

    def reset_conversation(self):
        self.conversation_history = []

def main():
    chatbot = AgriChatbot()

    print("Welcome to AgriChat! Ask me anything about agriculture, farming, or general questions.")
    print("Type 'quit' to exit, 'reset' to start a new conversation.")

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'reset':
            chatbot.reset_conversation()
            print("Conversation reset.")
            continue

        response = chatbot.chat(user_input)
        print(f"\nAgriChat: {response}")

if __name__ == "__main__":
    main()