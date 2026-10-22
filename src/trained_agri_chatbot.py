import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
import sys

class TrainedAgriChatbot:
    def __init__(self, model_path="./agri_model"):
        """
        Initialize the chatbot with a trained agricultural model

        Args:
            model_path: Path to the trained model directory
        """
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.conversation_history = []

        # System prompt for agricultural context
        self.system_prompt = """You are AgriChat, an AI assistant specialized in agriculture, farming, crop management, and agricultural economics.
        You help farmers with advice on crops, weather, pricing, and sustainable farming practices.
        Provide practical, helpful advice based on agricultural knowledge."""

        self.load_model()

    def load_model(self):
        """Load the trained model and tokenizer"""
        try:
            print(f"Loading model from {self.model_path}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_path)

            # Set pad token if not set
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            print("Model loaded successfully!")
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Falling back to basic mode...")
            self.model = None

    def format_conversation(self, user_message):
        """Format the conversation for the model input"""
        # Add system prompt and conversation history
        conversation = self.system_prompt + "\n\n"

        # Add conversation history (last few exchanges)
        for exchange in self.conversation_history[-4:]:  # Keep last 4 exchanges
            conversation += f"Human: {exchange['user']}\nAssistant: {exchange['assistant']}\n\n"

        # Add current user message
        conversation += f"Human: {user_message}\nAssistant:"

        return conversation

    def generate_response(self, user_message, max_length=150, temperature=0.7):
        """Generate a response using the trained model"""
        if self.model is None:
            return "Model not loaded. Please check the model path and try again."

        try:
            # Format input
            input_text = self.format_conversation(user_message)

            # Tokenize
            inputs = self.tokenizer(
                input_text,
                return_tensors="pt",
                truncation=True,
                max_length=256,
                padding=True
            )

            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    max_length=max_length,
                    num_return_sequences=1,
                    temperature=temperature,
                    do_sample=True,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )

            # Decode response
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extract just the assistant's response (after the last "Assistant:")
            if "Assistant:" in full_response:
                response = full_response.split("Assistant:")[-1].strip()
            else:
                response = full_response.replace(input_text, "").strip()

            # Clean up the response
            response = response.split("\nHuman:")[0].strip()  # Remove any following human input
            response = response.split("###")[0].strip()  # Remove any instruction markers

            return response if response else "I understand your question. Could you please provide more details?"

        except Exception as e:
            return f"Error generating response: {str(e)}"

    def chat(self, user_message):
        """Main chat method that maintains conversation history"""
        if not user_message or user_message.strip() == "":
            return "Please ask me something about agriculture!"

        # Generate response
        response = self.generate_response(user_message)

        # Add to conversation history
        self.conversation_history.append({
            "user": user_message,
            "assistant": response
        })

        # Keep only last 10 exchanges to avoid memory issues
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

        return response

    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = []
        print("Conversation history reset.")

    def get_conversation_history(self):
        """Get the current conversation history"""
        return self.conversation_history.copy()

# Global chatbot instance
_chatbot_instance = None

def get_agri_chatbot(model_path="./agri_model"):
    """Get or create the chatbot instance"""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = TrainedAgriChatbot(model_path)
    return _chatbot_instance

# For testing
if __name__ == "__main__":
    chatbot = get_agri_chatbot()

    print("AgriChat - Trained Agricultural Assistant")
    print("Type 'quit' to exit, 'reset' to clear conversation")
    print("-" * 50)

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'reset':
            chatbot.reset_conversation()
            print("Conversation reset.")
            continue
        elif user_input == "":
            continue

        response = chatbot.chat(user_input)
        print(f"AgriChat: {response}")
        print()