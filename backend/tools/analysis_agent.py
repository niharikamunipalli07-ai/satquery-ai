import os
import base64
from openai import OpenAI


def analyze_image(image_path: str, question: str):

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return {
            "success": False,
            "error": "OPENROUTER_API_KEY is not configured"
        }

    if not os.path.exists(image_path):
        return {
            "success": False,
            "error": "Image file not found"
        }

    try:

        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(
                image_file.read()
            ).decode("utf-8")

        extension = os.path.splitext(image_path)[1].lower()

        mime_type = "image/jpeg"

        if extension == ".png":
            mime_type = "image/png"
        elif extension in [".jpg", ".jpeg"]:
            mime_type = "image/jpeg"

        prompt = f"""
You are the Analysis Agent of SatQuery AI,
an intelligent satellite image analysis system.

Analyze the provided satellite image carefully.

User question:
{question}

Provide a clear and useful answer.

Focus on:
- buildings
- roads
- vegetation
- water bodies
- urban areas
- agricultural areas
- other visible geographical features

Do not invent information that cannot be seen in the image.
"""

        response = client.chat.completions.create(
             model="openrouter/free",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": (
                                    f"data:{mime_type};base64,"
                                    f"{image_data}"
                                )
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.2
        )

        if not response.choices:
            return {
                "success": False,
                "error": "Analysis model returned no response"
            }

        answer = response.choices[0].message.content

        if not answer:
            return {
                "success": False,
                "error": "Analysis model returned no text"
            }

        return {
            "success": True,
            "answer": answer
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }