# from typing import List
# from pydantic import BaseModel
# from openai import OpenAI

# # Define the structured output models
# class Subject(BaseModel):
#     subject: str
#     conditions: List[str]

# class Action(BaseModel):
#     action: str
#     subjects: List[Subject]

# class Actor(BaseModel):
#     actor: str
#     actions: List[Action]

# from dotenv import load_dotenv
# import os
# from openai import OpenAI

# load_dotenv()  # Load from .env file
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # Define the command to be parsed
# command = "Drone Alpha should survey the northern sector if visibility is clear."

# # Create the completion with structured output parsing
# completion = client.beta.chat.completions.parse(
#     model="gpt-4o-2024-08-06",
#     messages = [
#         {"role": "system", "content": (
#             "You are a drone command interpreter.\n"
#             "Extract structured data:\n"
#             "- actor: entity performing actions (e.g., 'Drone Alpha')\n"
#             "- action: specific operation to perform (e.g., 'survey', 'capture')\n"
#             "- subject: target or object of the action (e.g., 'northern sector', 'building roof')\n"
#             "- condition: situation under which action applies (e.g., 'if visibility is clear')\n"
#             "Structure output strictly according to the provided schema."
#         )},
#         {"role": "user", "content": command}
#     ],
#     response_format=List[Actor]
# )

# def parse_drone_command(command: str):
#     completion = client.beta.chat.completions.parse(
#         model="gpt-4o-2024-08-06",
#         messages=[
#             {"role": "system", "content": (
#                 "You are a drone command interpreter.\n"
#                 "Extract structured data:\n"
#                 "- actor: entity performing actions\n"
#                 "- action: specific operation\n"
#                 "- subject: target or object of the action\n"
#                 "- condition: situation under which action applies\n"
#                 "Output format: List of Actor objects."
#             )},
#             {"role": "user", "content": command}
#         ],
#         response_format=List[Actor]
#     )
#     return completion.choices[0].message.parsed

def parse_drone_command(command: str):
    pass