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
# FRONTEND
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static"
)


@app.get("/", include_in_schema=False)
async def home():
    return FileResponse(
        str(FRONTEND_DIR / "index.html")
    )


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "SatQuery AI"
    }


# ============================================================
# REQUEST MODEL
# ============================================================

class VQARequest(BaseModel):
    filename: str
    question: str


# ============================================================
# UPLOAD IMAGE
# ============================================================

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):

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

    filename = Path(file.filename).name

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename."
        )

    file_path = UPLOAD_DIR / filename

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
# VQA / GEO / ANALYSIS
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

    # Security: use only filename
    safe_filename = Path(filename).name

    image_path = UPLOAD_DIR / safe_filename

    if not image_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Uploaded image not found."
        )


    # ========================================================
    # STEP 1 — QUERY PLANNER
    # ========================================================

    try:

        from backend.tools.query_planner import classify_query

        planner_result = classify_query(question)

        print(
            "PLANNER RESULT:",
            planner_result
        )

    except Exception as e:

        print(
            "QUERY PLANNER ERROR:",
            str(e)
        )

        planner_result = {
            "success": False,
            "category": "VQA",
            "reason": "Planner failed. Using VQA as fallback.",
            "error": str(e)
        }


    # ========================================================
    # STEP 2 — GET CATEGORY
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


    category = str(category).upper().strip()

    if category not in ["VQA", "GEO", "ANALYSIS"]:

        category = "VQA"


    print(
        "SELECTED CATEGORY:",
        category
    )


    # ========================================================
    # STEP 3 — VQA AGENT
    # ========================================================

    if category == "VQA":

        try:

            from backend.tools.vqa import ask_vqa

            agent_result = ask_vqa(
                str(image_path),
                question
            )

        except Exception as e:

            print(
                "VQA AGENT ERROR:",
                str(e)
            )

            raise HTTPException(
                status_code=500,
                detail=f"VQA Agent error: {str(e)}"
            )


    # ========================================================
    # STEP 4 — GEO AGENT
    # ========================================================

    elif category == "GEO":

        try:

            from backend.tools.geo_agent import get_geo_information

            agent_result = get_geo_information(
                str(image_path)
            )

        except Exception as e:

            print(
                "GEO AGENT ERROR:",
                str(e)
            )

            raise HTTPException(
                status_code=500,
                detail=f"GEO Agent error: {str(e)}"
            )


    # ========================================================
    # STEP 5 — ANALYSIS AGENT
    # ========================================================

    elif category == "ANALYSIS":

        try:

            from backend.tools.analysis_agent import analyze_image

            agent_result = analyze_image(
                str(image_path),
                question
            )

        except Exception as e:

            print(
                "ANALYSIS AGENT ERROR:",
                str(e)
            )

            raise HTTPException(
                status_code=500,
                detail=f"Analysis Agent error: {str(e)}"
            )


    # ========================================================
    # STEP 6 — PROCESS AGENT RESULT
    # ========================================================

    if isinstance(agent_result, dict):

        success = agent_result.get(
            "success",
            True
        )

        if not success:

            error_message = agent_result.get(
                "error",
                "Agent failed."
            )

            return {
                "success": False,
                "category": category,
                "planner_reason": planner_reason,
                "answer": f"⚠️ {error_message}",
                "filename": safe_filename
            }


        answer = (
            agent_result.get("answer")
            or agent_result.get("content")
            or agent_result.get("response")
        )

        if not answer:

            answer = str(agent_result)

    else:

        answer = str(agent_result)


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