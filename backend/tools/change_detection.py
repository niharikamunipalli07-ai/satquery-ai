import os
import base64
from pathlib import Path

import cv2
import numpy as np
import requests
from dotenv import load_dotenv

load_dotenv()


OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"


def get_free_vision_models():
    """
    Get currently available free vision-language models
    from OpenRouter.
    """

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return []

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(
            OPENROUTER_MODELS_URL,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()
        models = data.get("data", [])

        selected_models = []

        for model in models:

            model_id = model.get("id", "")
            architecture = model.get("architecture", {})

            modalities = architecture.get(
                "input_modalities",
                []
            )

            pricing = model.get("pricing", {})

            prompt_price = pricing.get(
                "prompt",
                "1"
            )

            model_lower = model_id.lower()

            # Only free models
            is_free = (
                model_id.endswith(":free")
                or prompt_price == "0"
                or prompt_price == 0
                or prompt_price == "0.0"
            )

            # Must support images
            supports_image = "image" in modalities

            # Avoid safety/moderation models
            unwanted = [
                "safety",
                "moderation",
                "guard",
                "rerank",
                "embedding",
                "embed"
            ]

            is_unwanted = any(
                word in model_lower
                for word in unwanted
            )

            if (
                is_free
                and supports_image
                and not is_unwanted
            ):
                selected_models.append(model_id)

        return selected_models

    except Exception as e:
        print("MODEL DISCOVERY ERROR:", e)
        return []


def load_image(image_path):
    """
    Load image and convert it to RGB.
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

    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    return image


def calculate_change(image1, image2):
    """
    Calculate a basic pixel-level change map
    between two images.

    This is a baseline change-detection method.
    """

    # Resize second image to first image size
    image2 = cv2.resize(
        image2,
        (image1.shape[1], image1.shape[0])
    )

    # Convert to grayscale
    gray1 = cv2.cvtColor(
        image1,
        cv2.COLOR_RGB2GRAY
    )

    gray2 = cv2.cvtColor(
        image2,
        cv2.COLOR_RGB2GRAY
    )

    # Absolute difference
    difference = cv2.absdiff(
        gray1,
        gray2
    )

    # Reduce small image noise
    difference = cv2.GaussianBlur(
        difference,
        (5, 5),
        0
    )

    # Threshold
    _, change_mask = cv2.threshold(
        difference,
        30,
        255,
        cv2.THRESH_BINARY
    )

    # Morphological cleanup
    kernel = np.ones(
        (5, 5),
        np.uint8
    )

    change_mask = cv2.morphologyEx(
        change_mask,
        cv2.MORPH_OPEN,
        kernel
    )

    change_mask = cv2.morphologyEx(
        change_mask,
        cv2.MORPH_CLOSE,
        kernel
    )

    # Calculate percentage
    total_pixels = change_mask.size

    changed_pixels = np.count_nonzero(
        change_mask
    )

    change_percentage = (
        changed_pixels / total_pixels
    ) * 100

    return (
        change_mask,
        change_percentage
    )


def save_change_visualization(
    image1,
    image2,
    change_mask
):
    """
    Create and save a visual representation
    of detected changes.
    """

    output_dir = Path(
        "outputs/changes"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # Resize image2
    image2 = cv2.resize(
        image2,
        (image1.shape[1], image1.shape[0])
    )

    # Create visualization
    visualization = image2.copy()

    # Highlight changed pixels
    visualization[change_mask > 0] = [
        255,
        0,
        0
    ]

    # Convert RGB -> BGR
    visualization = cv2.cvtColor(
        visualization,
        cv2.COLOR_RGB2BGR
    )

    output_path = (
        output_dir /
        "change_detection_result.jpg"
    )

    cv2.imwrite(
        str(output_path),
        visualization
    )

    return str(output_path)


def encode_image(image_path):
    """
    Convert image into base64 data URL.
    """

    extension = Path(
        image_path
    ).suffix.lower()

    mime_type = "image/jpeg"

    if extension == ".png":
        mime_type = "image/png"

    elif extension == ".webp":
        mime_type = "image/webp"

    elif extension in [".jpg", ".jpeg"]:
        mime_type = "image/jpeg"

    with open(
        image_path,
        "rb"
    ) as file:

        image_data = base64.b64encode(
            file.read()
        ).decode("utf-8")

    return (
        f"data:{mime_type};base64,"
        f"{image_data}"
    )


def ask_change_description(
    image_path1,
    image_path2,
    question,
    models
):
    """
    Ask a vision-language model to describe
    the changes between two satellite images.
    """

    api_key = os.getenv(
        "OPENROUTER_API_KEY"
    )

    if not api_key:
        return {
            "success": False,
            "error": (
                "OPENROUTER_API_KEY "
                "is not configured"
            )
        }

    image1_data = encode_image(
        image_path1
    )

    image2_data = encode_image(
        image_path2
    )

    prompt = f"""
You are the Change Detection Agent
of SatQuery AI.

You are given two satellite images:

IMAGE 1 = earlier observation
IMAGE 2 = later observation

Compare the two images carefully.

User question:
{question}

Identify visible changes such as:

- newly constructed buildings
- demolished buildings
- road development
- vegetation changes
- agricultural changes
- water-body changes
- urban expansion
- land-use changes
- infrastructure changes

IMPORTANT:

Only describe changes that are reasonably
visible in the images.

Do not invent locations, dates,
coordinates, or objects.

Clearly distinguish between:
1. What changed
2. Where the change appears
3. Possible interpretation

Give a concise answer.
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    for model in models:

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
                                "url": image1_data
                            }
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image2_data
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
                OPENROUTER_API_URL,
                headers=headers,
                json=payload,
                timeout=120
            )

            print(
                "CHANGE MODEL:",
                model,
                "STATUS:",
                response.status_code
            )

            if response.status_code != 200:

                print(
                    "MODEL ERROR:",
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

                content = "\n".join(
                    text_parts
                )

            if content and content.strip():

                return {
                    "success": True,
                    "answer": content.strip(),
                    "model": model
                }

        except Exception as e:

            print(
                "CHANGE MODEL ERROR:",
                model,
                e
            )

            continue

    return {
        "success": False,
        "error": (
            "No available vision model "
            "could analyze the two images."
        )
    }


def detect_changes(
    image_path1,
    image_path2,
    question="What changed between these two satellite images?"
):
    """
    Main Change Detection Agent.

    Performs:
    1. Image validation
    2. Pixel-level change detection
    3. Change visualization
    4. Vision-language interpretation
    """

    try:

        if not os.path.exists(image_path1):
            return {
                "success": False,
                "error": "First image not found."
            }

        if not os.path.exists(image_path2):
            return {
                "success": False,
                "error": "Second image not found."
            }

        # Load images
        image1 = load_image(
            image_path1
        )

        image2 = load_image(
            image_path2
        )

        # Calculate changes
        change_mask, change_percentage = (
            calculate_change(
                image1,
                image2
            )
        )

        # Save visualization
        visualization_path = (
            save_change_visualization(
                image1,
                image2,
                change_mask
            )
        )

        # Get free vision models
        models = get_free_vision_models()

        # Fallback models
        if not models:

            models = [
                "google/gemma-4-31b-it:free",
                "google/gemma-4-26b-a4b-it:free",
                "minimax/minimax-m3:free"
            ]

        # Ask VLM
        ai_result = ask_change_description(
            image_path1,
            image_path2,
            question,
            models
        )

        if ai_result.get("success"):

            answer = ai_result.get(
                "answer",
                ""
            )

            model = ai_result.get(
                "model"
            )

        else:

            answer = (
                "Pixel-level analysis detected "
                f"approximately "
                f"{change_percentage:.2f}% "
                "changed area. "
                "The AI interpretation was unavailable."
            )

            model = None

        return {
            "success": True,
            "answer": answer,
            "change_percentage": round(
                change_percentage,
                2
            ),
            "visualization": visualization_path,
            "model": model
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }