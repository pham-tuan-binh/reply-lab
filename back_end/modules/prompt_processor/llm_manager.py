import os
from dotenv import load_dotenv

import google.generativeai as genai
from typing import List, Dict, Any

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../", ".env"))


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_LLM_MODEL = os.getenv("GEMINI_LLM_MODEL")

class LLMManager:
    def __init__(self, model_name: str = "gemini-1.5-pro", temperature: float = 0.0, verbose: bool = True):

        if "gemini" in model_name.lower():
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is missing in the environment variables")
            self.model = GoogleGeminiChatCompletions(
                api_key=GEMINI_API_KEY, model_name=model_name, temperature=temperature
            )
        else:
            raise NotImplementedError(f"Model {model_name} is not supported yet.")


class GoogleGeminiChatCompletions:
    def __init__(self, api_key: str, model_name="gemini-1.5-flash", max_tokens=3000, temperature=0.0):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.max_tokens = max_tokens
        self.temperature = temperature

    def infer(self, prompt, response_schema):

        response = self.model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json",
                               "response_schema": list[response_schema]}
        )

        return response