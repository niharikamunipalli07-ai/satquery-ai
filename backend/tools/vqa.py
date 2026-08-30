import base64
import os
import requests

from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def ask_vqa(image_path: str, question: str):

    if not OPENROUTER_API_KEY:
        return {
            "success": False,
            "error": "OPENROUTER_API_KEY is not configured"
        }

    try:

        # ==========================================
        # READ IMAGE
        # ==========================================

        with open(image_path, "rb") as image_file:

            image_data = base64.b64encode(
                image_file.read()
            ).decode("utf-8")


        # ==========================================
        # IMAGE TYPE
        # ==========================================

        extension = os.path.splitext(
            image_path
        )[1].lower()


        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".tif": "image/tiff",
            ".tiff": "image/tiff"
        }


        mime_type = mime_types.get(
            extension,
            "image/jpeg"
        )


        data_url = (
            f"data:{mime_type};base64,{image_data}"
        )


        # ==========================================
        # VQA PROMPT
        # ==========================================

        prompt = f"""
You are SatQuery AI, an AI assistant specialized
in satellite and remote-sensing image analysis.

Carefully inspect the provided satellite image.

Answer ONLY what can actually be observed
in the image.

User question:
{question}

Rules:

1. Describe visible objects clearly.
2. Identify buildings, roads, vegetation,
   fields, water bodies and other visible features.
3. Do not invent locations or objects.
4. Do not guess geographic coordinates.
5. If something cannot be determined from
   the image, say that it cannot be determined.
6. Give a clear and concise answer.
"""


        # ==========================================
        # OPENROUTER REQUEST
        # ==========================================

        response = requests.post(

            "https://openrouter.ai/api/v1/chat/completions",

            headers={
                "Authorization":
                    f"Bearer {OPENROUTER_API_KEY}",

                "Content-Type":
                    "application/json"
            },

            json={

                "model": "openrouter/free",

                "max_tokens": 1000,

                "messages": [

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

                                    "url": data_url
                                }
                            }

                        ]
                    }

                ]
            },

            timeout=120
        )


        # ==========================================
        # CHECK HTTP RESPONSE
        # ==========================================

        if response.status_code != 200:

            return {
                "success": False,
                "error":
                    f"OpenRouter HTTP {response.status_code}: "
                    f"{response.text}"
            }


        # ==========================================
        # PARSE JSON
        # ==========================================

        try:

            result = response.json()

        except Exception:

            return {
                "success": False,
                "error":
                    "OpenRouter returned invalid JSON: "
                    + response.text
            }


        # ==========================================
        # DEBUG RESPONSE
        # ==========================================

        print(
            "OPENROUTER RESPONSE:",
            result
        )


        # ==========================================
        # CHECK FOR API ERROR
        # ==========================================

        if "error" in result:

            error_info = result["error"]

            if isinstance(error_info, dict):

                return {
                    "success": False,
                    "error":
                        error_info.get(
                            "message",
                            str(error_info)
                        )
                }

            return {
                "success": False,
                "error": str(error_info)
            }


        # ==========================================
        # CHECK CHOICES
        # ==========================================

        if "choices" not in result:

            return {
                "success": False,
                "error":
                    "OpenRouter response does not contain "
                    "'choices'. Full response: "
                    + str(result)
            }


        if not result["choices"]:

            return {
                "success": False,
                "error":
                    "OpenRouter returned an empty choices list."
            }


        # ==========================================
        # GET MESSAGE
        # ==========================================

        message = result["choices"][0].get(
            "message",
            {}
        )


        content = message.get(
            "content"
        )


        if not content:

            return {
                "success": False,
                "error":
                    "AI returned no text content."
            }


        # ==========================================
        # SUCCESS
        # ==========================================

        return {

            "success": True,

            "question": question,

            "answer": content
        }


    except Exception as e:

        return {

            "success": False,

            "error": str(e)
        }