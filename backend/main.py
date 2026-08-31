from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = BASE_DIR / "frontend"
UPLOAD_DIR = BASE_DIR / "outputs" / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="SatQuery AI",
    description="Agentic Vision-Language Assistant for Remote Sensing",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# FRONTEND STATIC FILES
# ============================================================

# This makes:
#
# /static/script.js
# /static/style.css
#
# available to the browser.

app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static"
)


# ============================================================
# HOME PAGE
# ============================================================

@app.get("/", include_in_schema=False)
async def home():
    return FileResponse(
        str(FRONTEND_DIR / "index.html")
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "SatQuery AI"
    }


# ============================================================
# UPLOAD MODEL
# ============================================================

class VQARequest(BaseModel):
    filename: str
    question: str


# ============================================================
# UPLOAD IMAGE
# ============================================================

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):

    # Check file type
    if not file.content_type:
        raise HTTPException(
            status_code=400,
            detail="File type could not be detected."
        )

    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload an image file."
        )

    # Keep original filename
    filename = Path(file.filename).name

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename."
        )

    file_path = UPLOAD_DIR / filename

    # Read and save
    try:
        contents = await file.read()

        with open(file_path, "wb") as f:
            f.write(contents)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Could not save image: {str(e)}"
        )

    return {
        "success": True,
        "message": "Image uploaded successfully",
        "filename": filename
    }


# ============================================================
# VQA
# ============================================================

@app.post("/vqa")
async def vqa(request: VQARequest):

    filename = request.filename
    question = request.question.strip()

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required."
        )

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question is required."
        )

    # Make sure only the filename is used
    safe_filename = Path(filename).name

    image_path = UPLOAD_DIR / safe_filename

    if not image_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Uploaded image not found."
        )

    # ========================================================
    # QUERY PLANNER
    # ========================================================

    try:

        from backend.tools.query_planner import classify_query

        planner_result = classify_query(question)

    except Exception as e:

        print(
            "QUERY PLANNER ERROR:",
            str(e)
        )

        planner_result = None


    # ========================================================
    # EXTRACT CATEGORY
    # ========================================================

    category = "VQA"

    planner_reason = "Visual question answering"


    if isinstance(planner_result, dict):

        category = (
            planner_result.get("category")
            or planner_result.get("type")
            or planner_result.get("query_type")
            or "VQA"
        )

        planner_reason = (
            planner_result.get("reason")
            or planner_result.get("planner_reason")
            or planner_result.get("explanation")
            or "Visual question answering"
        )

    elif isinstance(planner_result, str):

        category = planner_result


    # ========================================================
    # VQA MODEL
    # ========================================================

    try:

        from backend.tools.vqa import ask_vqa

        # Your existing VQA function
        vqa_result = ask_vqa(
            str(image_path),
            question
        )

    except TypeError:

        # Some versions use keyword arguments
        try:

            vqa_result = ask_vqa(
                image_path=str(image_path),
                question=question
            )

        except Exception as e:

            print(
                "VQA ERROR:",
                str(e)
            )

            raise HTTPException(
                status_code=500,
                detail=str(e)
            )

    except Exception as e:

        print(
            "VQA ERROR:",
            str(e)
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


    # ========================================================
    # PROCESS VQA RESULT
    # ========================================================

    if isinstance(vqa_result, dict):

        answer = (
            vqa_result.get("answer")
            or vqa_result.get("content")
            or vqa_result.get("response")
        )

        # Preserve useful information
        if not answer:

            answer = str(vqa_result)

    else:

        answer = str(vqa_result)


    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {
        "success": True,
        "category": category,
        "planner_reason": planner_reason,
        "answer": answer,
        "filename": safe_filename
    }