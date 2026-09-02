import os
import cv2
import base64
import requests
import numpy as np
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def get_free_vision_models():
    """
    Get currently available free vision-capable models
    from OpenRouter.
    """

    if not OPENROUTER_API_KEY:
        return []

    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            timeout=20
        )

        if response.status_code != 200:
            return []

        models = response.json().get("data", [])
        result = []

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
            architecture = model.get("architecture", {})
            input_modalities = architecture.get(
                "input_modalities", []
            )

            if ":free" not in model_id:
                continue

            if "image" not in input_modalities:
                continue

            if any(
                word in model_id.lower()
                for word in blocked_words
            ):
                continue

            result.append(model_id)

        return result

    except Exception as e:
        print("OPTICAL-SAR MODEL DISCOVERY ERROR:", e)
        return []


def load_image(image_path):
    """
    Load an image using OpenCV.
    """

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(
            f"Unable to read image: {image_path}"
        )

    return image


def calculate_image_statistics(image):
    """
    Calculate basic image statistics.
    """

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    return {
        "width": int(image.shape[1]),
        "height": int(image.shape[0]),
        "channels": int(image.shape[2]),
        "mean_intensity": round(
            float(np.mean(gray)),
            2
        ),
        "standard_deviation": round(
            float(np.std(gray)),
            2
        ),
        "min_intensity": int(np.min(gray)),
        "max_intensity": int(np.max(gray))
    }


def create_comparison_image(
    optical_image,
    sar_image,
    output_path
):
    """
    Create a side-by-side comparison image.
    """

    height = max(
        optical_image.shape[0],
        sar_image.shape[0]
    )

    width1 = optical_image.shape[1]
    width2 = sar_image.shape[1]

    optical_resized = cv2.resize(
        optical_image,
        (width1, height)
    )

    sar_resized = cv2.resize(
        sar_image,
        (width2, height)
    )

    comparison = np.hstack(
        (optical_resized, sar_resized)
    )

    cv2.imwrite(
        output_path,
        comparison
    )

    return output_path


def encode_image(image_path):
    """
    Convert image to a base64 data URL.
    """

    with open(image_path, "rb") as file:
        encoded = base64.b64encode(
            file.read()
        ).decode("utf-8")

    extension = os.path.splitext(
        image_path
    )[1].lower()

    if extension in [".jpg", ".jpeg"]:
        mime_type = "image/jpeg"
    elif extension == ".png":
        mime_type = "image/png"
    elif extension in [".tif", ".tiff"]:
        mime_type = "image/tiff"
    else:
        mime_type = "image/jpeg"

    return f"data:{mime_type};base64,{encoded}"


def ask_optical_sar(
    optical_path,
    sar_path,
    question,
    models
):
    """
    Ask a vision-language model to analyze
    the optical + SAR image pair.
    """

    if not OPENROUTER_API_KEY:
        return {
            "success": False,
            "error": "OPENROUTER_API_KEY is not configured"
        }

    optical_data = encode_image(optical_path)
    sar_data = encode_image(sar_path)

    prompt = f"""
You are an expert remote-sensing image analysis assistant.

You are given two images:

1. Optical image
2. SAR image

Analyze them together.

Important instructions:
- Clearly distinguish observations from the optical image
  and observations from the SAR image.
- Identify visible land-cover, buildings, roads,
  vegetation, water bodies, agricultural areas,
  and other relevant structures when supported.
- Use SAR characteristics such as radar brightness,
  texture, and scattering patterns when appropriate.
- Do not invent geographic coordinates or locations.
- Do not claim an object exists unless there is visual evidence.
- If something cannot be determined, say so clearly.

User question:
{question}

Provide a concise but useful answer.
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    for model in models:

        print(
            "OPTICAL-SAR MODEL:",
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
                                "url": optical_data
                            }
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": sar_data
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 700
        }

        try:

            response = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=120
            )

            print(
                "OPTICAL-SAR STATUS:",
                response.status_code
            )

            if response.status_code != 200:
                print(
                    "OPTICAL-SAR ERROR:",
                    response.text[:500]
                )
                continue

            data = response.json()

            choices = data.get(
                "choices",
                []
            )

            if not choices:
                continue

            message = choices[0].get(
                "message",
                {}
            )

            content = message.get(
                "content"
            )

            if isinstance(content, list):
                text_parts = []

                for item in content:
                    if isinstance(item, dict):
                        text = item.get("text")

                        if text:
                            text_parts.append(text)

                content = "\n".join(
                    text_parts
                )

            if not content:
                continue

            content = str(content).strip()

            if len(content) < 10:
                continue

            return {
                "success": True,
                "answer": content,
                "model": model
            }

        except Exception as e:

            print(
                "OPTICAL-SAR MODEL ERROR:",
                str(e)
            )

            continue

    return {
        "success": False,
        "error": "No available vision model could analyze the optical-SAR pair"
    }


def analyze_optical_sar(
    optical_path,
    sar_path,
    question
):
    """
    Main Optical + SAR analysis function.
    """

    if not os.path.exists(optical_path):
        return {
            "success": False,
            "error": "Optical image not found"
        }

    if not os.path.exists(sar_path):
        return {
            "success": False,
            "error": "SAR image not found"
        }

    try:

        optical_image = load_image(
            optical_path
        )

        sar_image = load_image(
            sar_path
        )

        optical_stats = calculate_image_statistics(
            optical_image
        )

        sar_stats = calculate_image_statistics(
            sar_image
        )

        output_dir = "outputs/optical_sar"

        os.makedirs(
            output_dir,
            exist_ok=True
        )

        comparison_path = os.path.join(
            output_dir,
            "optical_sar_comparison.jpg"
        )

        create_comparison_image(
            optical_image,
            sar_image,
            comparison_path
        )

        models = get_free_vision_models()

        if not models:
            models = [
                "google/gemma-4-31b-it:free",
                "google/gemma-4-26b-a4b-it:free",
                "minimax/minimax-m3:free"
            ]

        ai_result = ask_optical_sar(
            optical_path,
            sar_path,
            question,
            models
        )

        if not ai_result.get("success"):
            return {
                "success": False,
                "error": ai_result.get(
                    "error",
                    "Optical-SAR analysis failed"
                ),
                "optical_statistics": optical_stats,
                "sar_statistics": sar_stats,
                "comparison": comparison_path
            }

        return {
            "success": True,
            "answer": ai_result["answer"],
            "model": ai_result.get("model"),
            "optical_statistics": optical_stats,
            "sar_statistics": sar_stats,
            "comparison": comparison_path
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }