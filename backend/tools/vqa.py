import base64
import os
import time
import requests

from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


# ============================================================
# SATQUERY AI - VQA
# ============================================================

def ask_vqa(image_path: str, question: str):

    # ========================================================
    # CHECK API KEY
    # ========================================================

    if not OPENROUTER_API_KEY:

        return {
            "success": False,
            "error": "OPENROUTER_API_KEY is not configured"
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
        # DETERMINE IMAGE TYPE
        # ====================================================

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


        # ====================================================
        # CREATE DATA URL
        # ====================================================

        data_url = (
            f"data:{mime_type};base64,{image_data}"
        )


        # ====================================================
        # SATQUERY AI PROMPT
        # ====================================================

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


        # ====================================================
        # MODELS TO TRY
        # ====================================================
        #
        # We try several models so that a temporary
        # provider rate-limit does not immediately
        # break SatQuery AI.
        #

        models = [

            "google/gemma-4-31b-it:free",

            "openrouter/free"

        ]


        last_error = None


        # ====================================================
        # TRY MODELS
        # ====================================================

        for model in models:

            print(
                f"SATQUERY AI: Trying model: {model}"
            )


            try:

                response = requests.post(

                    "https://openrouter.ai/api/v1/chat/completions",

                    headers={

                        "Authorization":
                            f"Bearer {OPENROUTER_API_KEY}",

                        "Content-Type":
                            "application/json",

                        "HTTP-Referer":
                            "https://satquery-ai-qpoi.onrender.com",

                        "X-Title":
                            "SatQuery AI"

                    },


                    json={

                        "model": model,

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


                # =================================================
                # SUCCESS
                # =================================================

                if response.status_code == 200:

                    try:

                        result = response.json()

                    except Exception:

                        last_error = (
                            "OpenRouter returned invalid JSON: "
                            + response.text
                        )

                        continue


                    print(
                        "OPENROUTER RESPONSE:",
                        result
                    )


                    # =============================================
                    # API ERROR INSIDE JSON
                    # =============================================

                    if "error" in result:

                        error_info = result["error"]


                        if isinstance(
                            error_info,
                            dict
                        ):

                            last_error = (
                                error_info.get(
                                    "message",
                                    str(error_info)
                                )
                            )

                        else:

                            last_error = str(
                                error_info
                            )

                        continue


                    # =============================================
                    # CHECK CHOICES
                    # =============================================

                    if "choices" not in result:

                        last_error = (
                            "OpenRouter response does not contain "
                            "'choices'. Full response: "
                            + str(result)
                        )

                        continue


                    if not result["choices"]:

                        last_error = (
                            "OpenRouter returned an empty "
                            "choices list."
                        )

                        continue


                    # =============================================
                    # GET MESSAGE
                    # =============================================

                    message = result["choices"][0].get(
                        "message",
                        {}
                    )


                    content = message.get(
                        "content"
                    )


                    if not content:

                        last_error = (
                            "AI returned no text content."
                        )

                        continue


                    # =============================================
                    # SUCCESSFUL ANSWER
                    # =============================================

                    print(
                        f"SATQUERY AI: Successful model: {model}"
                    )


                    return {

                        "success": True,

                        "question": question,

                        "answer": content,

                        "model": model

                    }


                # =================================================
                # RATE LIMIT
                # =================================================

                elif response.status_code == 429:

                    print(
                        f"SATQUERY AI: Model {model} "
                        "is rate-limited."
                    )

                    last_error = (
                        f"Model {model} is temporarily "
                        "rate-limited."
                    )

                    # Try next model
                    continue


                # =================================================
                # OTHER HTTP ERROR
                # =================================================

                else:

                    print(
                        f"SATQUERY AI: Model {model} "
                        f"returned HTTP {response.status_code}"
                    )


                    last_error = (
                        f"OpenRouter HTTP "
                        f"{response.status_code}: "
                        f"{response.text}"
                    )

                    continue


            except requests.exceptions.Timeout:

                last_error = (
                    f"Model {model} request timed out."
                )

                print(
                    "SATQUERY AI: Request timed out."
                )

                continue


            except requests.exceptions.RequestException as e:

                last_error = str(e)

                print(
                    "SATQUERY AI request error:",
                    e
                )

                continue


        # ========================================================
        # ALL MODELS FAILED
        # ========================================================

        return {

            "success": False,

            "error":
                "All available AI models are currently "
                "unavailable. Last error: "
                + str(last_error)

        }


    # ============================================================
    # GENERAL ERROR
    # ============================================================

    except Exception as e:

        print(
            "SATQUERY AI VQA ERROR:",
            e
        )


        return {

            "success": False,

            "error": str(e)

        }