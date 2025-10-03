🤖 TalentScout: AI Candidate Screener
---
TalentScout is a multi-stage, conversational HR assistant designed to streamline the initial candidate screening process. It uses the Google Gemini API (via LangChain) to gather essential information, dynamically generate relevant technical questions based on the candidate's provided tech stack, and manage the conversation state.

Currently, the application runs as a monolithic Streamlit web app where both the user interface and the core AI logic reside.

---

✨ Features (Current State)

Stateful Conversation: Tracks the conversation state (GREETING, GATHER_INFO, ASK_QUESTIONS, END) using Streamlit's session state.

Dynamic Question Generation: After collecting candidate background (name, role, tech stack), the system prompts the LLM to generate 3-5 technical screening questions specific to the declared technologies.

Monolithic Architecture: Simple to develop and run locally, as the UI and core logic are combined in a single Python script (app/main.py).

---

🛠️ Setup and Installation
Prerequisites
Python 3.10+

A Google Gemini API Key.

1. Clone the Repository
git clone https://github.com/raneAshutoshDs21/TalentScout_HRChatBot.git
cd TalentScout_HRChatBot

2. Virtual Environment & Dependencies
Activate your virtual environment (using the standard venv or conda).

**Create and activate venv (Windows example)**
python -m venv talent_scout
.\talent_scout\Scripts\activate

**Install dependencies (streamlit, google-genai, langchain, etc.)**
pip install -r requirements.txt

3. API Key Configuration
Create a file named .env in the project root directory (D:\talent_scout) and add your API key.

Code snippet

 **.env**
 
 GEMINI_API_KEY="AIzaSy...your...actual...key"

---

💻 Running the Application
Since the application is a Streamlit app, you must run it using the streamlit run command from the project root.

1. Execute the Frontend/Logic
Ensure your virtual environment is active, and run:
(talent_scout) PS D:\talent_scout> streamlit run app/main.py

This command will:

* Start a local web server (usually at http://localhost:8501).
* Run app/main.py, which initializes the TalentScoutAssistant class locally.
* Serve the interactive chat interface.

---

✅ Usage Guide
* Open the Streamlit URL provided in your console (e.g., http://localhost:8501).
* Start the conversation by entering your Full Name.
* The assistant will proceed through the Information Gathering stage. Provide details like your desired role, tech stack, and years of experience.

* At information gathering the input should be for instance, "My email id is abcd@gmail.com".

* When prompted, enter "NEXT" to transition to the Questioning phase, where dynamically generated questions will appear.

---

## 📂 Project Structure

The project follows a standard Python package structure, optimized for transition to a client-server architecture.

```text
talent_scout/
├── app/
│   ├── __init__.py           # Marks 'app' as a Python package
│   ├── chat_logic.py         # Core LLM logic (will become the API backend)
│   └── main.py               # Streamlit UI and local entry point
├── config/
│   ├── __init__.py           # Marks 'config' as a Python package
│   └── settings.py           # Configuration constants (API keys, states)
├── data/                     # Placeholder for files like PDFs or CSVs
├── .env                      # Stores GEMINI_API_KEY (ignored by Git)
├── .gitignore                # Specifies files/folders to exclude from version control
└── requirements.txt          # Project dependencies
```

---

➡️ Next Steps (To Be Implemented)
1. FastAPI Backend: Create app/api.py to expose chat_logic.py as a REST API.

2. Containerization: Create a Dockerfile for the FastAPI service.

3. Deployment: Deploy the Docker container to a service like Google Cloud Run.

4. Frontend Update: Modify app/main.py to be a client that makes HTTP requests to the deployed API.

