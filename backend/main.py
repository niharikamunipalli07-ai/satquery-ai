from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

from backend.api.upload import upload_image
from backend.tools.vqa import ask_vqa


# ==========================================
# CREATE FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="SatQuery AI",
    description="Agentic Vision-Language Assistant for Remote Sensing",
    version="1.0.0"
)


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# PATHS
# ==========================================

FRONTEND_DIR = Path("frontend")
UPLOAD_DIR = Path("outputs/uploads")

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================
# HOME PAGE
# ==========================================

@app.get("/")
async def home():

    frontend_file = FRONTEND_DIR / "index.html"

    if frontend_file.exists():
        return FileResponse(
            str(frontend_file)
        )

    return {
        "message": "Welcome to SatQuery AI",
        "status": "Backend is running",
        "error": "frontend/index.html not found"
    }


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "service": "SatQuery AI"
    }


# ==========================================
# UPLOAD IMAGE
# ==========================================

@app.post("/upload")
async def upload(
    file: UploadFile = File(...)
):

    try:

        return await upload_image(file)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==========================================
# VQA REQUEST MODEL
# ==========================================

class VQARequest(BaseModel):

    filename: str
    question: str


# ==========================================
# MAIN AI QUERY
# ==========================================

@app.post("/vqa")
async def vqa(
    request: VQARequest
):

    # ======================================
    # FIND IMAGE
    # ======================================

    image_path = (
        UPLOAD_DIR /
        request.filename
    )

    if not image_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Image not found"
        )


    # ======================================
    # QUERY PLANNER
    # ======================================

    from backend.tools.query_planner import (
        classify_query
    )


    question_lower = (
        request.question.lower()
    )


    # ======================================
    # KEYWORDS
    # ======================================

    visual_words = [
        "visible",
        "see",
        "shown",
        "image",
        "building",
        "buildings",
        "road",
        "roads",
        "vegetation",
        "green areas",
        "stadium",
        "sports facilities",
        "objects",
        "describe",
        "tree",
        "trees",
        "vehicle",
        "vehicles",
        "field",
        "fields"
    ]


    geo_words = [
        "latitude",
        "longitude",
        "coordinates",
        "gps",
        "geolocation",
        "geographic coordinates",
        "location",
        "city",
        "country",
        "address"
    ]


    analysis_words = [
        "analyze",
        "analysis",
        "urban development",
        "land-use",
        "land use",
        "change detection",
        "risk assessment",
        "pattern",
        "development",
        "compare",
        "comparison"
    ]


    # ======================================
    # CLASSIFY QUERY
    # ======================================

    if any(
        word in question_lower
        for word in analysis_words
    ):

        planner_result = {
            "success": True,
            "category": "ANALYSIS",
            "reason": (
                "The question asks for "
                "deeper image analysis."
            )
        }


    elif any(
        word in question_lower
        for word in geo_words
    ):

        planner_result = {
            "success": True,
            "category": "GEO",
            "reason": (
                "The question asks for "
                "geographic information."
            )
        }


    elif any(
        word in question_lower
        for word in visual_words
    ):

        planner_result = {
            "success": True,
            "category": "VQA",
            "reason": (
                "The question asks about "
                "visually observable features."
            )
        }


    else:

        planner_result = classify_query(
            request.question
        )


    # ======================================
    # CHECK PLANNER
    # ======================================

    if not planner_result.get(
        "success",
        False
    ):

        raise HTTPException(
            status_code=500,
            detail=planner_result.get(
                "error",
                "Query planning failed"
            )
        )


    category = planner_result.get(
        "category",
        "VQA"
    )


    # ======================================
    # VQA AGENT
    # ======================================

    if category == "VQA":

        try:

            result = ask_vqa(
                str(image_path),
                request.question
            )

        except Exception as e:

            error_message = str(e)

            # OpenRouter rate limit
            if "429" in error_message:

                raise HTTPException(
                    status_code=429,
                    detail=(
                        "OpenRouter daily AI request "
                        "limit has been reached. "
                        "Please try again after the "
                        "daily limit resets."
                    )
                )

            raise HTTPException(
                status_code=500,
                detail=error_message
            )


        if not result.get(
            "success",
            False
        ):

            error_message = result.get(
                "error",
                "VQA processing failed"
            )

            if "429" in error_message:

                raise HTTPException(
                    status_code=429,
                    detail=(
                        "OpenRouter daily AI request "
                        "limit has been reached. "
                        "Please try again later."
                    )
                )

            raise HTTPException(
                status_code=500,
                detail=error_message
            )


        return {
            "success": True,
            "category": "VQA",
            "planner_reason": planner_result.get(
                "reason",
                ""
            ),
            "answer": result.get(
                "answer",
                ""
            )
        }


    # ======================================
    # GEO AGENT
    # ======================================

    if category == "GEO":

        try:

            from backend.tools.geo_agent import (
                get_geo_information
            )

            geo_result = get_geo_information(
                str(image_path)
            )

        except Exception as e:

            raise HTTPException(
                status_code=500,
                detail=str(e)
            )


        if not geo_result.get(
            "success",
            False
        ):

            raise HTTPException(
                status_code=500,
                detail=geo_result.get(
                    "error",
                    "GEO analysis failed"
                )
            )


        return {
            "success": True,
            "category": "GEO",
            "planner_reason": planner_result.get(
                "reason",
                ""
            ),
            "geo_information": geo_result
        }


    # ======================================
    # ANALYSIS AGENT
    # ======================================

    if category == "ANALYSIS":

        try:

            from backend.tools.analysis_agent import (
                analyze_image
            )

            analysis_result = analyze_image(
                str(image_path),
                request.question
            )

        except Exception as e:

            raise HTTPException(
                status_code=500,
                detail=str(e)
            )


        if not analysis_result.get(
            "success",
            False
        ):

            raise HTTPException(
                status_code=500,
                detail=analysis_result.get(
                    "error",
                    "Analysis failed"
                )
            )


        return {
            "success": True,
            "category": "ANALYSIS",
            "planner_reason": planner_result.get(
                "reason",
                ""
            ),
            "answer": analysis_result.get(
                "answer",
                ""
            )
        }


    # ======================================
    # UNKNOWN CATEGORY
    # ======================================

    return {
        "success": False,
        "error": "Unknown query category"
    }


# ==========================================
# SERVE FRONTEND STATIC FILES
# ==========================================

if FRONTEND_DIR.exists():

    app.mount(
        "/frontend",
        StaticFiles(
            directory=str(FRONTEND_DIR),
            html=True
        ),
        name="frontend"
    )