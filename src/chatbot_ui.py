import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(__file__))
from chatbot import AgriChatbot

st.set_page_config(page_title="AgriChat - AI Assistant", page_icon="🌾")

st.title("🌾 AgriChat - Your AI Agricultural Assistant")
st.markdown("Ask me anything about farming, crops, weather, pricing, and sustainable agriculture!")

# Initialize chatbot in session state
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = AgriChatbot()

if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me about agriculture..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get bot response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.chatbot.chat(prompt)
        st.markdown(response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar with controls
with st.sidebar:
    st.header("Chat Controls")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.chatbot.reset_conversation()
        st.rerun()

    st.markdown("---")
    st.markdown("**Model:** llama-3.2-3b-instruct")
    st.markdown("**API:** http://192.168.31.36:1234")

    st.markdown("---")
    st.markdown("**Sample Questions:**")
    st.markdown("- What crops should I grow this season?")
    st.markdown("- How to improve soil fertility?")
    st.markdown("- Best practices for pest control?")
    st.markdown("- Market trends for rice prices?")