from pathlib import Path
from PIL import Image


ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff"
}


def validate_image(file_path: str):

    path = Path(file_path)

    # Check whether file exists
    if not path.exists():
        return {
            "valid": False,
            "error": "File does not exist"
        }

    # Check extension
    extension = path.suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        return {
            "valid": False,
            "error": "Unsupported image format"
        }

    # Try opening the image
    try:
        with Image.open(path) as image:

            width, height = image.size

            return {
                "valid": True,
                "filename": path.name,
                "format": image.format,
                "width": width,
                "height": height,
                "mode": image.mode
            }

    except Exception as e:

        return {
            "valid": False,
            "error": f"Unable to read image: {str(e)}"
        }