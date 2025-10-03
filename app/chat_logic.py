
import json
import os
from typing import List, Dict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from config.settings import GEMINI_API_KEY, GEMINI_MODEL_NAME, State


# ==============================================================================
# 1. Pydantic Schemas for Structured Output
# ==============================================================================

class CandidateInfo(BaseModel):
    """Schema to detect and confirm initial candidate information."""
    full_name: str = Field(description="The candidate's full name.")
    email_address: str = Field(description="The candidate's primary email address.")
    phone_number: str = Field(description="The candidate's primary phone number.")
    years_of_experience: float = Field(description="Total years of professional experience, e.g., 5.0")
    desired_positions: List[str] = Field(description="A list of job titles the candidate is interested in.")
    current_location: str = Field(description="The candidate's current city and country.")
    tech_stack: List[str] = Field(description="A list of key technologies, frameworks, and languages.")

class TechQuestion(BaseModel):
    """A single technical question."""
    question: str = Field(description="A specific technical question related to the technology.")

class TechAssessment(BaseModel):
    """Schema for generating technical questions grouped by technology."""
    assessment: Dict[str, List[TechQuestion]] = Field(
        description="A dictionary where keys are the technologies (e.g., 'Python') and values are a list of 3-5 relevant TechQuestion objects."
    )


# ==============================================================================
# 2. Embedded Prompts
# ==============================================================================

INFO_GATHERING_PROMPT = """
**ROLE**: You are "TalentScout Hiring Assistant," an intelligent, professional, and friendly chatbot.
**GOAL**: Conduct the initial screening by gathering essential information from the candidate.

--- INSTRUCTION ---
1.  **Sequential Gathering**: Ask for **ONE** piece of information at a time. Start with the **Full Name**.
2.  **Confirmation and Transition**: Once you believe you have collected the entire **Tech Stack**, you must conclude with this specific phrase: "Thank you for providing your details. We are now moving to the **Technical Assessment Stage**. Your tech stack is: [list tech stack]. Please type 'NEXT' to confirm this is correct and proceed, or update your tech stack now."
3.  **Exit Handling**: If the candidate types "quit," "bye," "exit," or "end," conclude the conversation gracefully.

Conversation History: {history}
Candidate Input: {user_input}
"""

TECH_QUESTIONS_PROMPT_TEMPLATE = """
**ROLE**: You are "TalentScout Tech Assessor," a highly skilled technical interviewer.
**GOAL**: Generate 3 to 5 challenging, relevant, and concise technical screening questions for each technology listed in the provided Tech Stack.

--- INPUT DATA ---
Candidate's Tech Stack: {tech_stack}

--- INSTRUCTION ---
1.  **Constraint**: You MUST generate exactly **3 to 5 questions** for **EACH** technology item listed.
2.  **Format**: You MUST output a single JSON object that strictly adheres to the provided output schema.

--- OUTPUT SCHEMA ---
{format_instructions}
"""


# ==============================================================================
# 3. Core Assistant Class
# ==============================================================================

class TalentScoutAssistant:
    def __init__(self):
        if not os.getenv("GEMINI_API_KEY"):
             raise ValueError("GEMINI_API_KEY not set.")
        
        # Initialize the LLM
        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL_NAME, 
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.2
        )
        
        # Initialize Conversation Memory
        self.memory = ConversationBufferWindowMemory(
            memory_key="history",
            input_key="user_input",
            return_messages=True,
            k=8
        )
        
        # Information Gathering Chain (LLMChain)
        self.info_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(INFO_GATHERING_PROMPT),
            memory=self.memory,
            verbose=False
        )

        # Tech Assessment setup
        self.assessment_parser = PydanticOutputParser(pydantic_object=TechAssessment)
        self.tech_prompt = PromptTemplate(
            template=TECH_QUESTIONS_PROMPT_TEMPLATE,
            input_variables=["tech_stack"],
            partial_variables={"format_instructions": self.assessment_parser.get_format_instructions()},
        )
        
        self.current_question_index: int = 0
        self.all_questions_list: List[str] = []
        self.user_answers: Dict[str, str] = {}


    def _extract_tech_stack_from_history(self) -> List[str]:
        """Uses a targeted LLM call to extract the final tech stack."""
        extraction_prompt = f"""
        Analyze the following conversation history and extract ONLY the list of key technologies, 
        frameworks, languages, databases, and tools the candidate declared they are proficient in. 
        Return the result as a comma-separated list of technologies.
        
        Conversation History: {str(self.memory.load_memory_variables({})['history'])}
        """
        try:
            response = self.llm.invoke(extraction_prompt).content
            return [t.strip() for t in response.split(',') if t.strip()]
        except Exception:
            return ["Python", "SQL"] # Fallback

    def _generate_technical_questions(self, tech_stack: List[str]) -> Dict:
        """Generates structured technical questions using PydanticOutputParser."""
        tech_stack_str = ", ".join(tech_stack)
        prompt_value = self.tech_prompt.format_prompt(tech_stack=tech_stack_str)
        response = self.llm.invoke(prompt_value.to_messages())
        
        try:
            parsed_output = self.assessment_parser.parse(response.content)
            self.tech_questions = parsed_output.assessment
            for questions in self.tech_questions.values():
                self.all_questions_list.extend([q.question for q in questions])
            return self.tech_questions
        except Exception:
            return None

    def _get_next_question(self) -> str:
        """Retrieves the next question from the flattened list."""
        if self.current_question_index < len(self.all_questions_list):
            question = self.all_questions_list[self.current_question_index]
            self.current_question_index += 1
            return question
        else:
            return None
            
    def _end_conversation(self, final_state: str) -> str:
        """Gracefully concludes the conversation."""
        return (
            "Thank you for completing the initial screening with TalentScout Hiring Assistant. "
            "Your information has been securely recorded. Goodbye and good luck!"
        )

    def process_user_input(self, user_input: str, current_state: str) -> tuple[str, str]:
        """Main function to process user input and manage the state machine."""
        
        if user_input.lower() in ["quit", "bye", "exit", "end"]:
            return self._end_conversation(State.END), State.END

        if current_state == State.GREETING:
            response = self.info_chain.run(user_input=user_input)
            return response, State.GATHER_INFO

        elif current_state == State.GATHER_INFO:
            
            # Check for transition command *only after* the LLM has presented the transition phrase
            history_str = self.memory.load_memory_variables({})['history'][-1].content.lower() if self.memory.load_memory_variables({})['history'] else ""
            
            if "next" in user_input.lower() and "technical assessment stage" in history_str:
                
                tech_stack = self._extract_tech_stack_from_history()
                self._generate_technical_questions(tech_stack)
                
                if self.all_questions_list:
                    first_question = self._get_next_question()
                    return f"Excellent. We have {len(self.all_questions_list)} questions. **Question 1:** {first_question}", State.ASK_QUESTIONS
                else:
                    return "I apologize, question generation failed. Ending conversation.", State.END

            # Continue gathering (run the conversational chain)
            response = self.info_chain.run(user_input=user_input)
            return response, State.GATHER_INFO

        elif current_state == State.ASK_QUESTIONS:
            self.user_answers[f"Q{self.current_question_index}"] = user_input
            next_question = self._get_next_question()
            
            if next_question:
                q_num = self.current_question_index + 1
                return f"Thank you for your answer. \n\n**Question {q_num}:** {next_question}", State.ASK_QUESTIONS
            else:
                return self._end_conversation(State.END), State.END

        else:
            return "I did not understand. Can you please repeat?", current_state
