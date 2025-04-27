from typing import List
from pydantic import BaseModel
import os
from llm_manager import LLMManager
import json
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../", ".env"))


GEMINI_LLM_MODEL = os.getenv("GEMINI_LLM_MODEL")

llm_manager = LLMManager(model_name=GEMINI_LLM_MODEL, temperature=0.0, verbose=True)


# Define the structured output models
class Subject(BaseModel):
    subject: str
    conditions: List[str]

class Action(BaseModel):
    action: str
    subjects: List[Subject]

class Actor(BaseModel):
    actor: str
    actions: List[Action]

client = llm_manager.model

# write a function to accept user input and return the response
def process_user_input(user_query: str) -> dict:
    """Process a command using the LLM and return the structured data."""
    try:
        response = client.infer(
            prompt=user_query,
            response_schema=Actor
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error processing user input: {str(e)}")
        return {"error": str(e)}