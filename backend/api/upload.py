from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import shutil

from backend.tools.image_validator import validate_image
from backend.tools.geotiff_reader import read_geotiff


router = APIRouter()

UPLOAD_DIR = Path("outputs/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff"
}


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected"
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use JPG, JPEG, PNG, TIF or TIFF."
        )

    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    validation = validate_image(str(file_path))

    if not validation["valid"]:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail=validation["error"]
        )

    response = {
        "message": "Image uploaded and validated successfully",
        "filename": file.filename,
        "file_type": extension,
        "path": str(file_path),
        "image_info": validation
    }

    if extension in {".tif", ".tiff"}:

        try:
            geotiff_info = read_geotiff(str(file_path))

            response["geotiff_info"] = geotiff_info

        except Exception as e:

            response["geotiff_info"] = {
                "error": f"Unable to read GeoTIFF information: {str(e)}"
            }
    return response