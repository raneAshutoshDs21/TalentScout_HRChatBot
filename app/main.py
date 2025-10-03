import streamlit as st
import os
import sys
import time

# Correctly import constants from the config module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import GEMINI_API_KEY, State

# Correctly import the TalentScoutAssistant class from the app module
from app.chat_logic import TalentScoutAssistant


# --- Configuration and Initialization ---

# Define the conversational states used in the project
# Ensure these match the States defined in your TalentScoutAssistant's process_user_input
State.GREETING = "GREETING"
State.GATHER_INFO = "GATHER_INFO"
State.ASK_QUESTIONS = "ASK_QUESTIONS"
State.END = "END"


def initialize_session_state():
    """Sets up the initial Streamlit session state."""
    
    # 1. Initialize the Assistant Object
    if State.LOGIC_AGENT not in st.session_state:
        try:
            # Initialize the LangChain object only once
            st.session_state[State.LOGIC_AGENT] = TalentScoutAssistant()
        except ValueError:
            # Handle the case where the API key is not set
            st.session_state[State.LOGIC_AGENT] = None
    
    # 2. Initialize the Conversation History
    if State.MESSAGES not in st.session_state:
        st.session_state[State.MESSAGES] = []
        
    # 3. Initialize the State Machine
    if 'current_state' not in st.session_state:
        st.session_state['current_state'] = State.GREETING
        
        # Add the first message (greeting)
        st.session_state[State.MESSAGES].append(
            {"role": "assistant", "content": "Hello! I am **TalentScout Hiring Assistant**. I'll guide you through our initial screening. Please provide your **Full Name** to begin."}
        )


# --- Core Logic and UI ---

def main():
    st.set_page_config(
        page_title="TalentScout HR Assistant",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    st.title("🤖 TalentScout: AI Candidate Screener")

    # --- API Key Check ---
    # We check environment variables, which should be loaded from .env by python-dotenv
    if not os.getenv("GEMINI_API_KEY"):
        st.error("❌ **ERROR**: GEMINI_API_KEY not found. Please check your `.env` file.")
        return

    # Initialize the required state variables
    initialize_session_state()
    agent = st.session_state[State.LOGIC_AGENT]
    
    if agent is None: # Second check for failed initialization
        st.error("❌ **ERROR**: Failed to initialize the Assistant. Check configuration or API key.")
        return

    # --- Display Conversation ---
    for message in st.session_state[State.MESSAGES]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- User Input Handling ---
    if st.session_state['current_state'] != State.END:
        
        # Enable input if the conversation is ongoing
        if prompt := st.chat_input("Enter your information or response...", disabled=False):
            
            # 1. Add user message to state and display
            st.session_state[State.MESSAGES].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # 2. Get AI Response
            with st.chat_message("assistant"):
                with st.spinner("Processing response..."):
                    
                    # Call the main backend function to process the input and determine the next state
                    ai_response_text, new_state = agent.process_user_input(
                        user_input=prompt,
                        current_state=st.session_state['current_state']
                    )
                    
                    # Update state and display response
                    st.session_state['current_state'] = new_state
                    st.session_state[State.MESSAGES].append(
                        {"role": "assistant", "content": ai_response_text}
                    )
                    st.markdown(ai_response_text)
                    
            # Rerun to update the input field state 
            st.rerun() 
            
    else:
        st.info("✅ This conversation has concluded. Thank you for your time!")


if __name__ == "__main__":
    # Note: If running locally in VS Code, ensure your virtual environment 
    # is active and run: streamlit run app/main.py
    main()