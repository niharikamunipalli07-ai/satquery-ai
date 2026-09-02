import os
import base64
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
# GET FREE VISION MODELS
# ============================================================

def get_free_vision_models():

    if not OPENROUTER_API_KEY:
        return []

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:

        response = requests.get(
            MODELS_URL,
            headers=headers,
            params={
                "input_modalities": "image",
                "max_price": "0"
            },
            timeout=30
        )

        if response.status_code != 200:
            print(
                "MODEL LIST ERROR:",
                response.status_code
            )
            return []

        data = response.json()

        models = data.get("data", [])

        vision_models = []

        blocked_words = [
            "safety",
            "content-safety",
            "moderation",
            "guard",
            "rerank",
            "embedding",
            "embed"
        ]

        for model in models:

            model_id = model.get("id", "")

            if not model_id:
                continue

            if ":free" not in model_id:
                continue

            model_name = model_id.lower()

            if any(
                word in model_name
                for word in blocked_words
            ):
                continue

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
            "AVAILABLE FREE ANALYSIS MODELS:",
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
# ANALYSIS AGENT
# ============================================================

def analyze_image(image_path: str, question: str):

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
        # IMAGE TYPE
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
        # ANALYSIS PROMPT
        # ====================================================

        prompt = f"""
You are the Analysis Agent of SatQuery AI,
an intelligent satellite image analysis system.

Analyze the provided satellite image carefully.

User question:
{question}

Provide a clear and useful analytical answer.

Focus on:

- buildings
- roads
- vegetation
- water bodies
- urban areas
- agricultural areas
- land-use patterns
- spatial patterns
- infrastructure
- other visible geographical features

Important rules:

1. Answer the user's question directly.
2. Base the answer only on visible information.
3. Do not invent objects.
4. Do not invent coordinates.
5. Do not guess an exact geographic location.
6. Clearly mention uncertainty when something cannot
   be determined from the image.
7. For analysis questions, explain the visible pattern
   or relationship when possible.
8. Do not perform safety classification.
9. Do not output "User Safety: safe".
10. Return only the analytical answer.
"""


        # ====================================================
        # GET AVAILABLE MODELS
        # ====================================================

        models = get_free_vision_models()


        # ====================================================
        # FALLBACK MODELS
        # ====================================================

        if not models:

            models = [
                "google/gemma-4-31b-it:free",
                "google/gemma-4-26b-a4b-it:free"
            ]


        # ====================================================
        # TRY EACH MODEL
        # ====================================================

        last_error = None


        for model in models:

            print(
                "SATQUERY AI ANALYSIS: Trying model:",
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
                                    "url": data_url
                                }
                            }

                        ]
                    }

                ],

                "max_tokens": 1000,

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
                        "ANALYSIS MODEL RATE-LIMITED:",
                        model
                    )

                    last_error = (
                        f"{model} is rate-limited"
                    )

                    continue


                # =================================================
                # MODEL UNAVAILABLE
                # =================================================

                if response.status_code == 404:

                    print(
                        "ANALYSIS MODEL UNAVAILABLE:",
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
                # PARSE JSON
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
                        "ANALYSIS MODEL ERROR:",
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
                        "Analysis model returned no response"
                    )

                    continue


                # =================================================
                # GET MESSAGE
                # =================================================

                message = choices[0].get(
                    "message",
                    {}
                )


                answer = message.get(
                    "content"
                )


                if not answer:

                    last_error = (
                        "Analysis model returned no text"
                    )

                    continue


                # =================================================
                # HANDLE LIST CONTENT
                # =================================================

                if isinstance(
                    answer,
                    list
                ):

                    text_parts = []

                    for item in answer:

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

                    answer = " ".join(
                        text_parts
                    )


                answer = str(
                    answer
                ).strip()


                # =================================================
                # PREVENT SAFETY RESPONSE
                # =================================================

                safety_responses = [

                    "user safety: safe",

                    "user safety: unsafe",

                    "safe",

                    "unsafe"
                ]


                if answer.lower() in safety_responses:

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
                    "SATQUERY AI ANALYSIS SUCCESS"
                )

                print(
                    "MODEL:",
                    selected_model
                )

                print(
                    "ANSWER:",
                    answer
                )

                print(
                    "===================================="
                )


                return {

                    "success": True,

                    "answer": answer,

                    "model": selected_model
                }


            except requests.exceptions.Timeout:

                print(
                    "ANALYSIS TIMEOUT:",
                    model
                )

                last_error = (
                    f"{model} request timed out"
                )

                continue


            except requests.exceptions.RequestException as e:

                print(
                    "ANALYSIS NETWORK ERROR:",
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
                "rate-limited.",

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