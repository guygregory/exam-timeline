"""Run this model in Python

> pip install openai
"""
import os
from openai import OpenAI
import json

# To authenticate with the model you will need to generate a personal access token (PAT) in your GitHub settings. 
# Create your PAT token by following instructions here: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
client = OpenAI(
    #base_url="https://models.github.ai/inference",
    base_url="https://models.inference.ai.azure.com",

    api_key=os.environ["GITHUB_TOKEN"],
)

# Read in the text from passed_exams.csv
with open("passed_exams.csv", "r", encoding="utf-8") as f:
    passed_exams_text = f.read()

# Read in the text from priority_ARB_exams.csv
with open("priority_ARB_exams.csv", "r", encoding="utf-8") as f:
    priority_exams_text = [exam.strip() for exam in f.read().strip().split(",")]

response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are an AI assistant, which recommends the next logical Microsoft exam, based on the Microsoft learner's existing transcript. Take into account only the most recent exams when considering their next step. Also take into account current technology trends. Ensure the exam you return is not already on their transcript, as an exam can't be taken twice.",
        },
        {
            "role": "user",
            "content": passed_exams_text,
        }
    ],
    model="gpt-4o",
    temperature=0,
    max_tokens=4096,
    top_p=1,
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "exam_code",
            "schema": {
                "type": "object",
                "properties": {
                    "exam_code": {
                        "type": "string",
                        "description": "A valid Microsoft exam code; must be one from a pre-defined list.",
                        "enum": priority_exams_text
                    }
                },
                "required": [
                    "exam_code"
                ],
                "additionalProperties": False
            },
            "strict": True
        }
    }
)

# Get the response content and parse it
response_content = response.choices[0].message.content
print(response_content)

# Parse the JSON response and update the partial file
try:
    recommendation_data = json.loads(response_content)
    exam_code = recommendation_data.get("exam_code", "-")
    
    # Update the partial file with the exam code
    with open("partials/ai-recommendation.html", "w", encoding="utf-8") as f:
        f.write(f'<span id="ai-recommendation">{exam_code}</span>')
    
    print(f"Updated partials/ai-recommendation.html with exam code: {exam_code}")
    
except (json.JSONDecodeError, KeyError) as e:
    print(f"Error parsing recommendation response: {e}")
    # Keep the default "-" in case of error
    with open("partials/ai-recommendation.html", "w", encoding="utf-8") as f:
        f.write('<span id="ai-recommendation">-</span>')
