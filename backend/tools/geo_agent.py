import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_geo_information(image_path: str):

    path = Path(image_path)

    if not path.exists():
        return {
            "success": False,
            "error": "Image file not found"
        }

    try:
        # Try to read GeoTIFF metadata
        from backend.tools.geotiff_reader import read_geotiff

        geo_data = read_geotiff(str(path))

        if geo_data and isinstance(geo_data, dict):

            return {
                "success": True,
                "answer": format_geo_answer(geo_data),
                "metadata": geo_data
            }

        # Normal JPEG/PNG images usually do not contain
        # latitude/longitude information.
        return {
            "success": True,
            "answer": (
                "Geographic coordinates could not be determined "
                "from this image. The uploaded image does not "
                "contain readable GPS/latitude/longitude metadata."
            ),
            "metadata": {}
        }

    except Exception as e:

        return {
            "success": True,
            "answer": (
                "Geographic coordinates could not be determined "
                "from this image. It appears that the uploaded "
                "image does not contain readable geospatial metadata."
            ),
            "metadata": {
                "error": str(e)
            }
        }


def format_geo_answer(data):

    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if latitude is not None and longitude is not None:

        return (
            f"Latitude: {latitude}\n"
            f"Longitude: {longitude}"
        )

    coordinates = data.get("coordinates")

    if coordinates:

        return f"Coordinates: {coordinates}"

    return (
        "The image contains no readable latitude/longitude "
        "coordinates in its available geospatial metadata."
    )