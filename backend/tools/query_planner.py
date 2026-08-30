import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)


def classify_query(question: str):

    if not OPENROUTER_API_KEY:
        return {
            "success": False,
            "error": "OPENROUTER_API_KEY is not configured"
        }

    prompt = """
You are the Query Planner for SatQuery AI.

Classify the user's question into exactly ONE category:

VQA
GEO
ANALYSIS

IMPORTANT RULES:

VQA:
Use VQA when the user asks what is visible in the image,
or asks to describe objects, buildings, roads, vegetation,
stadiums, vehicles, fields, structures, colors, shapes,
or other visual features.

Examples:
"What is visible in this satellite image?"
"Are there buildings in the image?"
"Describe the roads and vegetation."
"What sports facilities are visible?"
"Describe only the buildings, roads and green areas."

GEO:
Use GEO ONLY when the user asks for geographic or location information,
such as latitude, longitude, coordinates, GPS, location, city,
country, address, or geospatial metadata.

Examples:
"What are the coordinates?"
"What is the latitude and longitude?"
"Where was this image captured?"
"Does this image contain GPS information?"

ANALYSIS:
Use ANALYSIS when the user asks for deeper interpretation,
comparison, patterns, land-use analysis, urban development,
change detection, risk assessment, or other analytical conclusions.

IMPORTANT:
If a question asks what can be SEEN in the image, classify it as VQA.
Do NOT classify a question as GEO merely because the image is a satellite image.

Return JSON only:

{
    "category": "VQA",
    "reason": "The question asks about visible objects in the image."
}
"""

    try:

        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {
                    "role": "user",
                    "content": prompt + "\n\nUser question:\n" + question
                }
            ],
            max_tokens=300
        )

        content = response.choices[0].message.content

        if not content:
            return {
                "success": False,
                "error": "Planner model returned no text content"
            }

        content = content.strip()

        # Remove markdown code fences if the model adds them
        if content.startswith("```"):
            content = content.replace("```json", "")
            content = content.replace("```", "")
            content = content.strip()

        result = json.loads(content)

        category = result.get("category", "").upper()

        if category not in ["VQA", "GEO", "ANALYSIS"]:
            return {
                "success": False,
                "error": "Invalid category returned by planner"
            }

        return {
            "success": True,
            "category": category,
            "reason": result.get("reason", "")
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }