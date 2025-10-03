import os
from dotenv import load_dotenv

# Load environment variables from a local .env file (standard for VS Code/local)
load_dotenv()

# Configuration constants
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
GEMINI_MODEL_NAME = "gemini-2.5-flash-lite" # Fast conversational model

# Conversation state flags for the State Machine
class State:
    GREETING = "greeting"
    GATHER_INFO = "gather_info"
    ASK_QUESTIONS = "ask_questions"
    END = "end"
    LOGIC_AGENT = "logic_agent"
    MESSAGES = "messages"
