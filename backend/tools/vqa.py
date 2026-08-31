import base64
import os
import requests

from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def ask_vqa(image_path: str, question: str):

    # ============================================================
    # CHECK API KEY
    # ============================================================

    if not OPENROUTER_API_KEY:
        return {
            "success": False,
            "error": "OPENROUTER_API_KEY is not configured"
        }

    # ============================================================
    # CHECK IMAGE
    # ============================================================

    if not os.path.exists(image_path):
        return {
            "success": False,
            "error": "Image file not found"
        }

    try:

        # ========================================================
        # READ IMAGE
        # ========================================================

        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(
                image_file.read()
            ).decode("utf-8")

        # ========================================================
        # IMAGE TYPE
        # ========================================================

        extension = os.path.splitext(image_path)[1].lower()

        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
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

        # ========================================================
        # PROMPT
        # ========================================================

        prompt = f"""
You are SatQuery AI, a Vision-Language Assistant
specialized in satellite and remote-sensing image analysis.

Carefully inspect the satellite image.

User question:
{question}

Rules:

1. Answer the question directly.
2. Describe only things actually visible.
3. Identify buildings, roads, vegetation, fields,
   water bodies, stadiums, vehicles and structures
   when relevant.
4. Do not invent objects.
5. Do not invent coordinates.
6. Do not guess an exact location.
7. If something cannot be determined, say so.
8. Give a clear and concise answer.
9. Do NOT perform safety classification.
10. Do NOT output "User Safety: safe".
11. Return only the actual answer.
"""

        # ========================================================
        # MODEL FALLBACKS
        # ========================================================
        #
        # OpenRouter can try the next model if the first model
        # fails or is rate-limited.
        #
        # ========================================================

        models = [
            "google/gemma-4-26b-a4b-it:free",
            "google/gemma-4-31b-it:free"
        ]

        # ========================================================
        # OPENROUTER REQUEST
        # ========================================================

        response = requests.post(

            "https://openrouter.ai/api/v1/chat/completions",

            headers={
                "Authorization":
                    f"Bearer {OPENROUTER_API_KEY}",

                "Content-Type":
                    "application/json"
            },

            json={

                # Primary model
                "model": models[0],

                # OpenRouter model-level fallback
                "models": models,

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
                ],

                "max_tokens": 1000,

                "temperature": 0.2
            },

            timeout=120
        )

        # ========================================================
        # DEBUG
        # ========================================================

        print(
            "OPENROUTER STATUS:",
            response.status_code
        )

        print(
            "OPENROUTER RESPONSE:",
            response.text
        )

        # ========================================================
        # HTTP ERROR
        # ========================================================

        if response.status_code != 200:

            return {
                "success": False,

                "error":
                    f"OpenRouter HTTP "
                    f"{response.status_code}: "
                    f"{response.text}"
            }

        # ========================================================
        # JSON
        # ========================================================

        try:

            result = response.json()

        except Exception:

            return {
                "success": False,

                "error":
                    "OpenRouter returned invalid JSON."
            }

        # ========================================================
        # API ERROR
        # ========================================================

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

        # ========================================================
        # CHOICES
        # ========================================================

        if "choices" not in result:

            return {
                "success": False,

                "error":
                    "OpenRouter response does not contain choices."
            }

        if not result["choices"]:

            return {
                "success": False,

                "error":
                    "OpenRouter returned an empty choices list."
            }

        # ========================================================
        # MESSAGE
        # ========================================================

        message = result["choices"][0].get(
            "message",
            {}
        )

        content = message.get("content")

        # ========================================================
        # CONTENT
        # ========================================================

        if not content:

            return {
                "success": False,

                "error":
                    "AI returned no text content."
            }

        content = content.strip()

        # ========================================================
        # PREVENT SAFETY MODEL RESPONSE
        # ========================================================

        if content.lower() in [
            "user safety: safe",
            "user safety: unsafe",
            "safe",
            "unsafe"
        ]:

            return {
                "success": False,

                "error":
                    "The selected model returned a safety "
                    "classification instead of an image answer."
            }

        # ========================================================
        # SUCCESS
        # ========================================================

        print(
            "SATQUERY AI: VQA answer generated successfully."
        )

        return {

            "success": True,

            "question": question,

            "answer": content,

            "model": result.get(
                "model",
                "unknown"
            )
        }

    # ============================================================
    # TIMEOUT
    # ============================================================

    except requests.exceptions.Timeout:

        return {
            "success": False,

            "error":
                "OpenRouter request timed out. "
                "Please try again."
        }

    # ============================================================
    # NETWORK ERROR
    # ============================================================

    except requests.exceptions.RequestException as e:

        return {
            "success": False,

            "error":
                f"Network error: {str(e)}"
        }

    # ============================================================
    # OTHER ERROR
    # ============================================================

    except Exception as e:

        return {
            "success": False,

            "error": str(e)
        }