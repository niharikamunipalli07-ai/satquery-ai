import base64
import os
import requests

from dotenv import load_dotenv

load_dotenv()

# ============================================================
# OPENROUTER CONFIGURATION
# ============================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS_URL = "https://openrouter.ai/api/v1/models"


# ============================================================
# GET AVAILABLE FREE VISION MODELS
# ============================================================

def get_free_vision_models():
    """
    Get currently available free models from OpenRouter
    that support image input.
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(
            MODELS_URL,
            headers=headers,
            params={
                "input_modalities": "image",
                "max_price": "0",
            },
            timeout=30,
        )

        if response.status_code != 200:
            print(
                "MODEL LIST STATUS:",
                response.status_code
            )
            return []

        data = response.json()

        models = data.get("data", [])

        vision_models = []

        # Words used to exclude unsuitable models
        blocked_words = [
            "safety",
            "content-safety",
            "moderation",
            "guard",
            "rerank",
            "embedding",
            "embed",
        ]

        for model in models:

            model_id = model.get("id", "")

            if not model_id:
                continue

            # Only free model variants
            if ":free" not in model_id:
                continue

            model_name = model_id.lower()

            # Avoid safety/moderation models
            if any(
                word in model_name
                for word in blocked_words
            ):
                continue

            # Check modalities
            architecture = model.get(
                "architecture",
                {}
            )

            input_modalities = architecture.get(
                "input_modalities",
                []
            )

            if "image" not in input_modalities:
                continue

            vision_models.append(model_id)

        print(
            "AVAILABLE FREE VISION MODELS:",
            vision_models
        )

        return vision_models

    except Exception as e:

        print(
            "MODEL DISCOVERY ERROR:",
            str(e)
        )

        return []


# ============================================================
# VQA FUNCTION
# ============================================================

def ask_vqa(image_path: str, question: str):

    # ========================================================
    # CHECK API KEY
    # ========================================================

    if not OPENROUTER_API_KEY:

        return {
            "success": False,
            "error":
                "OPENROUTER_API_KEY is not configured"
        }


    # ========================================================
    # CHECK IMAGE
    # ========================================================

    if not os.path.exists(image_path):

        return {
            "success": False,
            "error": "Image file not found"
        }


    try:

        # ====================================================
        # READ IMAGE
        # ====================================================

        with open(
            image_path,
            "rb"
        ) as image_file:

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

            ".jpg":
                "image/jpeg",

            ".jpeg":
                "image/jpeg",

            ".png":
                "image/png",

            ".webp":
                "image/webp",

            ".tif":
                "image/tiff",

            ".tiff":
                "image/tiff"
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


        # ====================================================
        # FIND CURRENT FREE VISION MODELS
        # ====================================================

        models = get_free_vision_models()


        # ====================================================
        # FALLBACK IF MODEL DISCOVERY FAILS
        # ====================================================

        if not models:

            models = [

                "google/gemma-4-31b-it:free",

                "google/gemma-4-26b-a4b-it:free"
            ]


        # ====================================================
        # TRY MODELS ONE BY ONE
        # ====================================================

        last_error = None


        for model in models:

            print(
                "SATQUERY AI: Trying model:",
                model
            )


            payload = {

                "model": model,

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

                                    "url":
                                        data_url
                                }
                            }
                        ]
                    }
                ],

                "max_tokens": 700,

                "temperature": 0.2
            }


            try:

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


                print(
                    "OPENROUTER STATUS:",
                    response.status_code
                )


                # =================================================
                # RATE LIMIT
                # =================================================

                if response.status_code == 429:

                    print(
                        "MODEL RATE-LIMITED:",
                        model
                    )

                    last_error = (
                        f"{model} is rate-limited"
                    )

                    continue


                # =================================================
                # MODEL NOT AVAILABLE
                # =================================================

                if response.status_code == 404:

                    print(
                        "MODEL NOT AVAILABLE:",
                        model
                    )

                    last_error = (
                        f"{model} is unavailable"
                    )

                    continue


                # =================================================
                # OTHER HTTP ERROR
                # =================================================

                if response.status_code != 200:

                    print(
                        "OPENROUTER ERROR:",
                        response.text
                    )

                    last_error = (
                        f"HTTP {response.status_code}: "
                        f"{response.text}"
                    )

                    continue


                # =================================================
                # PARSE RESPONSE
                # =================================================

                try:

                    result = response.json()

                except Exception:

                    last_error = (
                        "OpenRouter returned invalid JSON"
                    )

                    continue


                # =================================================
                # API ERROR
                # =================================================

                if "error" in result:

                    error_info = result["error"]

                    if isinstance(
                        error_info,
                        dict
                    ):

                        error_message = (
                            error_info.get(
                                "message",
                                str(error_info)
                            )
                        )

                    else:

                        error_message = str(
                            error_info
                        )


                    print(
                        "MODEL ERROR:",
                        error_message
                    )


                    last_error = error_message

                    continue


                # =================================================
                # CHECK CHOICES
                # =================================================

                choices = result.get(
                    "choices"
                )


                if not choices:

                    last_error = (
                        "OpenRouter returned no choices"
                    )

                    continue


                # =================================================
                # GET CONTENT
                # =================================================

                message = choices[0].get(
                    "message",
                    {}
                )


                content = message.get(
                    "content"
                )


                if not content:

                    last_error = (
                        "AI returned no text content"
                    )

                    continue


                # =================================================
                # HANDLE CONTENT FORMAT
                # =================================================

                if isinstance(
                    content,
                    list
                ):

                    text_parts = []

                    for item in content:

                        if isinstance(
                            item,
                            dict
                        ):

                            text = item.get(
                                "text"
                            )

                            if text:

                                text_parts.append(
                                    text
                                )

                    content = " ".join(
                        text_parts
                    )


                content = str(
                    content
                ).strip()


                # =================================================
                # SAFETY RESPONSE CHECK
                # =================================================

                safety_responses = [

                    "user safety: safe",

                    "user safety: unsafe",

                    "safe",

                    "unsafe"
                ]


                if content.lower() in safety_responses:

                    print(
                        "UNSUITABLE SAFETY RESPONSE:",
                        model
                    )

                    last_error = (
                        "Model returned a safety "
                        "classification"
                    )

                    continue


                # =================================================
                # SUCCESS
                # =================================================

                selected_model = result.get(
                    "model",
                    model
                )


                print(
                    "===================================="
                )

                print(
                    "SATQUERY AI VQA SUCCESS"
                )

                print(
                    "MODEL:",
                    selected_model
                )

                print(
                    "ANSWER:",
                    content
                )

                print(
                    "===================================="
                )


                return {

                    "success": True,

                    "question": question,

                    "answer": content,

                    "model": selected_model
                }


            except requests.exceptions.Timeout:

                print(
                    "TIMEOUT:",
                    model
                )

                last_error = (
                    f"{model} request timed out"
                )

                continue


            except requests.exceptions.RequestException as e:

                print(
                    "NETWORK ERROR:",
                    model,
                    str(e)
                )

                last_error = str(e)

                continue


        # ========================================================
        # ALL MODELS FAILED
        # ========================================================

        return {

            "success": False,

            "error":
                "All available free vision models "
                "are currently unavailable or "
                "rate-limited. Please try again later.",

            "details":
                last_error
        }


    # ========================================================
    # GENERAL ERROR
    # ========================================================

    except Exception as e:

        return {

            "success": False,

            "error": str(e)
        }