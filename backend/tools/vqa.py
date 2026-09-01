import base64
import os
import requests

from dotenv import load_dotenv

load_dotenv()

# ============================================================

# OPENROUTER API KEY

# ============================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ============================================================

# VQA FUNCTION

# ============================================================

def ask_vqa(image_path: str, question: str):

```
# --------------------------------------------------------
# CHECK API KEY
# --------------------------------------------------------

if not OPENROUTER_API_KEY:

    return {
        "success": False,
        "error": "OPENROUTER_API_KEY is not configured"
    }


# --------------------------------------------------------
# CHECK IMAGE
# --------------------------------------------------------

if not os.path.exists(image_path):

    return {
        "success": False,
        "error": "Image file not found"
    }


try:

    # ====================================================
    # READ IMAGE
    # ====================================================

    with open(image_path, "rb") as image_file:

        image_data = base64.b64encode(
            image_file.read()
        ).decode("utf-8")


    # ====================================================
    # DETECT IMAGE TYPE
    # ====================================================

    extension = os.path.splitext(
        image_path
    )[1].lower()


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


    # ====================================================
    # PROMPT
    # ====================================================

    prompt = f"""
```

You are SatQuery AI, a Vision-Language Assistant
specialized in satellite and remote-sensing image analysis.

Carefully inspect the provided satellite image.

User question:
{question}

Instructions:

1. Answer the user's question directly.
2. Describe ONLY what can actually be observed.
3. Identify buildings, roads, vegetation, fields,
   water bodies, stadiums, vehicles and structures
   when relevant.
4. Do not invent objects.
5. Do not invent coordinates.
6. Do not guess an exact geographic location.
7. If something cannot be determined from the image,
   clearly say that it cannot be determined.
8. Keep the answer clear and concise.
9. Do NOT perform safety classification.
10. Do NOT output "User Safety: safe".
11. Return ONLY the actual satellite-image answer.
    """

    ```
    # ====================================================
    # MODEL FALLBACK CHAIN
    # ====================================================
    #
    # OpenRouter will try these models in order.
    #
    # The models parameter is OpenRouter's documented
    # model-level fallback mechanism.
    #
    # ====================================================

    models = [

        "google/gemma-4-31b-it:free",

        "google/gemma-4-26b-a4b-it:free"

    ]


    # ====================================================
    # REQUEST
    # ====================================================

    payload = {

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

    }


    response = requests.post(

        OPENROUTER_URL,

        headers={

            "Authorization":
                f"Bearer {OPENROUTER_API_KEY}",

            "Content-Type":
                "application/json"

        },

        json=payload,

        timeout=120

    )


    # ====================================================
    # DEBUG
    # ====================================================

    print(
        "OPENROUTER STATUS:",
        response.status_code
    )

    print(
        "OPENROUTER RAW RESPONSE:",
        response.text
    )


    # ====================================================
    # HANDLE HTTP ERRORS
    # ====================================================

    if response.status_code == 429:

        return {

            "success": False,

            "error":
                "OpenRouter is temporarily rate-limited. "
                "Please wait a little and try again."

        }


    if response.status_code == 404:

        return {

            "success": False,

            "error":
                "The selected vision model is currently "
                "unavailable. Please try again later."

        }


    if response.status_code != 200:

        return {

            "success": False,

            "error":
                f"OpenRouter HTTP {response.status_code}: "
                f"{response.text}"

        }


    # ====================================================
    # PARSE JSON
    # ====================================================

    try:

        result = response.json()

    except Exception:

        return {

            "success": False,

            "error":
                "OpenRouter returned invalid JSON."

        }


    # ====================================================
    # CHECK API ERROR
    # ====================================================

    if "error" in result:

        error_info = result["error"]

        if isinstance(error_info, dict):

            error_message = error_info.get(
                "message",
                str(error_info)
            )

        else:

            error_message = str(error_info)


        return {

            "success": False,

            "error": error_message

        }


    # ====================================================
    # CHECK CHOICES
    # ====================================================

    choices = result.get("choices")

    if not choices:

        return {

            "success": False,

            "error":
                "OpenRouter returned no choices."

        }


    # ====================================================
    # GET MESSAGE
    # ====================================================

    message = choices[0].get(
        "message",
        {}
    )


    content = message.get(
        "content"
    )


    # ====================================================
    # CHECK CONTENT
    # ====================================================

    if not content:

        return {

            "success": False,

            "error":
                "AI returned no text content."

        }


    content = content.strip()


    # ====================================================
    # PREVENT SAFETY-MODEL RESPONSE
    # ====================================================

    safety_responses = [

        "user safety: safe",

        "user safety: unsafe",

        "safe",

        "unsafe"

    ]


    if content.lower() in safety_responses:

        return {

            "success": False,

            "error":
                "The selected model returned a safety "
                "classification instead of a satellite "
                "image answer."

        }


    # ====================================================
    # SUCCESS
    # ====================================================

    selected_model = result.get(
        "model",
        "unknown"
    )


    print(
        "SATQUERY AI: VQA answer generated successfully."
    )

    print(
        "SATQUERY AI: Model used:",
        selected_model
    )


    return {

        "success": True,

        "question": question,

        "answer": content,

        "model": selected_model

    }
    ```

    # ========================================================

    # TIMEOUT

    # ========================================================

    except requests.exceptions.Timeout:

    ```
    return {

        "success": False,

        "error":
            "OpenRouter request timed out. "
            "Please try again."

    }
    ```

    # ========================================================

    # NETWORK ERROR

    # ========================================================

    except requests.exceptions.RequestException as e:

    ```
    return {

        "success": False,

        "error":
            f"Network error: {str(e)}"

    }
    ```

    # ========================================================

    # OTHER ERROR

    # ========================================================

    except Exception as e:

    ```
    return {

        "success": False,

        "error":
            str(e)

    }
    ```
